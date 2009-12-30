from __future__ import with_statement

import datetime
import os

from edwin.models.photo import Photo

class _FSProperty(object):
    _to_python = _from_python = lambda self, x: x

    def __init__(self, name):
        self.name = name

    def __get__(self, album, cls=None):
        fpath = os.path.join(album.path, '.%s' % self.name)
        if os.path.exists(fpath):
            return self._to_python(open(fpath).read())

    def __set__(self, album, value):
        fpath = os.path.join(album.path, '.%s' % self.name)
        if value is None:
            if os.path.exists(fpath):
                os.remove(fpath)
        else:
            with open(fpath, 'w') as f:
                f.write(self._from_python(value))

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
    desc = _FSProperty('desc')
    date_range = _DateRangeFSProperty('date_range')

    def __init__(self, path):
        self.path = path

        if self.date_range is None:
            self._guess_date_range()

    def __getitem__(self, fname):
        fpath = os.path.join(self.path, fname)
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

    def keys(self):
        for fname in os.listdir(self.path):
            if fname.startswith('.'):
                continue

            lower = fname.lower()
            if lower.endswith('.jpg') or lower.endswith('.jpeg'):
                yield fname

            path = os.path.join(self.path, fname)
            if os.path.isdir(path):
                yield fname

    def values(self):
        for fname in self.keys():
            yield self.__getitem__(fname)

    def photo_names(self):
        for fname in os.listdir(self.path):
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
            self.date_range = earliest, latest