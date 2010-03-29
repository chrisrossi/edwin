from __future__ import with_statement

import datetime
import os
import pickle

from happy.acl import ALL_PERMISSIONS
from happy.acl import Allow
from happy.acl import Deny
from happy.acl import Everyone

from edwin.models.photo import Photo

class _FSProperty(object):
    _to_python = _from_python = lambda self, x: x

    def __init__(self, name):
        self.name = name

    def __get__(self, album, cls=None):
        fpath = os.path.join(album.fspath, '.%s' % self.name)
        if os.path.exists(fpath):
            return self._to_python(open(fpath).read())

    def __set__(self, album, value):
        fpath = os.path.join(album.fspath, '.%s' % self.name)
        if value is None:
            if os.path.exists(fpath):
                os.remove(fpath)
        else:
            with open(fpath, 'w') as f:
                f.write(self._from_python(value))

class _PickleProperty(_FSProperty):
    _to_python = lambda self, x: pickle.loads(x)
    _from_python = lambda self, x: pickle.dumps(x)


class _DateRangeFSProperty(_FSProperty):
    def _to_python(self, s):
        def to_date(date_s):
            args = map(int, date_s.split('-'))
            return datetime.date(*args)
        return tuple(map(to_date, s.split(',')))

    def _from_python(self, value):
        return ','.join(
            ['%04d-%02d-%02d' % (d.year, d.month, d.day) for d in value]
        )

class Album(object):
    title = _FSProperty('title')
    location = _FSProperty('location')
    desc = _FSProperty('desc')
    date_range = _DateRangeFSProperty('date_range')
    _acl = _PickleProperty('_acl')

    def __init__(self, path):
        self.fspath = path

        if self.date_range is None:
            self.date_range = self._guess_date_range()

        if self._acl is None:
            self.update_acl()

    def __getitem__(self, fname):
        fpath = os.path.join(self.fspath, fname)
        if os.path.isfile(fpath):
            photo = Photo(fpath)
            photo.__name__ = fname
            photo.__parent__ = self
            return photo

        if os.path.isdir(fpath):
            album = Album(fpath)
            album.__name__ = fname
            album.__parent__ = self
            return album

        raise KeyError(fname)

    def __contains__(self, fname):
        fpath = os.path.join(self.fspath, fname)
        return os.path.exists(fpath)

    def keys(self):
        for fname in os.listdir(self.fspath):
            if fname.startswith('.'):
                continue

            lower = fname.lower()
            if lower.endswith('.jpg') or lower.endswith('.jpeg'):
                yield fname

            path = os.path.join(self.fspath, fname)
            if os.path.isdir(path):
                yield fname

    def values(self):
        for fname in self.keys():
            yield self.__getitem__(fname)

    def photo_names(self):
        for fname in os.listdir(self.fspath):
            if fname.startswith('.'):
                continue

            lower = fname.lower()
            if lower.endswith('.jpg') or lower.endswith('.jpeg'):
                yield fname

    def has_photos(self):
        try:
            self.photo_names().next()
            return True
        except StopIteration:
            return False

    def photos(self):
        for fname in self.photo_names():
            yield self.__getitem__(fname)

    def update_date_range(self):
        cur = self.date_range
        new = self._guess_date_range()

        if cur is None or new[0] < cur[0] or new[1] > cur[1]:
            # Some piece of the new range sticks outside of the old range,
            # so update the range
            self.date_range = new

    def _guess_date_range(self):
        earliest = latest = None
        for item in self.values():
            if isinstance(item, Photo):
                date = item.date
                if date is None:
                    continue
                if earliest is None:
                    earliest = latest = date
                elif date < earliest:
                    earliest = date
                elif date > latest:
                    latest = date
            else:
                date_range = item.date_range
                if date_range is None:
                    continue
                start, end = date_range
                if earliest is None:
                    earliest, latest = start, end
                else:
                    if start < earliest:
                        earliest = start
                    elif end > latest:
                        latest = end

        if earliest is not None:
            return earliest, latest

    def visibility(self):
        visibilities = set([child.visibility for child in self.photos()])
        if 'public' in visibilities:
            return 'public'
        elif 'new' in visibilities:
            return 'new'
        return 'private'

    @property
    def new(self):
        for child in self.photos():
            if child.visibility == 'new':
                return True
        return False

    def update_acl(self):
        if self.has_photos() and self.visibility() != 'public':
            self._acl = [
                (Allow, 'group.Administrators', ALL_PERMISSIONS),
                (Deny, Everyone, ALL_PERMISSIONS)
            ]
        else:
            self._acl = []

    __acl__ = _acl
