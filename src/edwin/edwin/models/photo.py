from happy.acl import ALL_PERMISSIONS
from happy.acl import Allow
from happy.acl import Deny
from happy.acl import Everyone

import copy
import datetime
from edwin.models.metadata import Metadata
import Image
from jpeg import jpeg
import os
import re

date_folder_re = re.compile('.*(\d\d\d\d).(\d\d?).(\d\d?).*')

class _MetadataProperty(object):
    _serial = _deserial = lambda self, x: x

    def __init__(self, name, default=None):
        self.name = name
        self.default = default

    def __get__(self, photo, cls=None):
        if self.name in photo._metadata:
            return self._deserial(photo._metadata[self.name])
        return copy.copy(self.default)

    def __set__(self, photo, value):
        if value is None:
            if self.name in photo._metadata:
                del photo._metadata[self.name]
        else:
            photo._metadata[self.name] = self._serial(value)

class _TupleMetadataProperty(_MetadataProperty):
    def _deserial(self, l):
        return tuple(l)

class _DateMetadataProperty(_MetadataProperty):
    def _serial(self, value):
        if value is not None:
            return '-'.join(map(str, [value.year, value.month, value.day]))

    def _deserial(self, value):
        if value is not None:
            parts = map(int, value.split('-'))
            return datetime.date(*parts)

class _ExifProperty(object):
    _to_python = lambda self, x: x

    def __init__(self, id):
        self.id = id

    def __get__(self, photo, cls=None):
        exif = getattr(photo, '_exif', None)
        if exif is None:
            exif_tags = jpeg.getExif(photo.fpath)
            if exif_tags is None:
                exif = []
            else:
                exif = exif_tags.exif
            photo._exif = exif
        for tag in exif:
            if tag.intID == self.id:
                return self._to_python(tag.value)

class _TimestampExifProperty(_ExifProperty):
    DATETIME_FORMAT = '%Y:%m:%d %H:%M:%S'

    def _to_python(self, value):
        try:
            return datetime.datetime.strptime(value, self.DATETIME_FORMAT)
        except ValueError:
            return None

class Photo(object):
    SW_VERSION = 1

    id = _MetadataProperty('id')
    version = _MetadataProperty('version', 0)
    title = _MetadataProperty('title')
    location = _MetadataProperty('location')
    photographer = _MetadataProperty('photographer')
    desc = _MetadataProperty('desc')
    visibility = _MetadataProperty('visibility', 'new')
    timestamp = _TimestampExifProperty(0x9003)
    date = _DateMetadataProperty('date')
    tags = _MetadataProperty('tags', default=[])
    size = _TupleMetadataProperty('size')
    _rotation = _MetadataProperty('rotation', 0)

    def __init__(self, fpath):
        self.fpath = fpath
        self._metadata = Metadata(fpath)

        if self.date is None:
            self.date = self._guess_date()

        if self.size is None:
            image = Image.open(self.fpath)
            self.size = image.size

        self._evolve()

    def _transformed_path(self):
        return '%s.transformed.jpg' % self.fpath

    @property
    def modified(self):
        return os.path.getmtime(self.fpath)

    @property
    def image(self):
        transformed_path = self._transformed_path()
        if os.path.exists(transformed_path):
            return Image.open(transformed_path)

        # Do non-destructive transformations (preserve original file)
        image = Image.open(self.fpath)
        transformed = False

        rotation = self._rotation
        if rotation != 0:
            image = image.rotate(rotation)
            transformed = True

        if transformed:
            image.save(transformed_path)

        return image

    def rotate(self, angle):
        # Set angle of rotation
        self._rotation = (self._rotation + angle) % 360

        # Force transformations to be reapplied
        transformed_path = self._transformed_path()
        if os.path.exists(transformed_path):
            os.remove(transformed_path)

        # Get new size from transformed image
        self.size = self.image.size

    def _guess_date(self):
        # First see if date is contained in folder structure
        dirname = os.path.dirname(self.fpath)
        match = date_folder_re.match(dirname)
        if match is not None:
            parts = map(int, match.groups())
            return datetime.date(*parts)

        t = self.timestamp
        if t is not None:
            return datetime.date(t.year, t.month, t.day)

    @property
    def __acl__(self):
        if self.visibility != 'public':
            return [
                (Allow, 'group.Administrators', ALL_PERMISSIONS),
                (Deny, Everyone, ALL_PERMISSIONS),
            ]
        return [] # inherit

    def _evolve(self):
        if self.version != self.SW_VERSION:
            for step in xrange(self.version + 1, self.SW_VERSION + 1):
                methodname = '_evolve%d' % step
                method = getattr(self, methodname)
                method()
        self.version = self.SW_VERSION

    def _evolve1(self):
        metadata = self._metadata
        if 'published' in metadata:
            if metadata['published']:
                self.visibility = 'public'
            else:
                self.visibility = 'private'
            del metadata['published']

