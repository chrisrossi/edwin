import datetime
from edwin.models.metadata import Metadata
from jpeg import jpeg

class _MetadataProperty(object):
    _to_python = lambda self, x: x

    def _from_python(self, value):
        if isinstance(value, basestring):
            return value
        return str(value)

    def __init__(self, name, default=None):
        self.name = name
        self.default = default

    def __get__(self, photo, cls=None):
        return self._to_python(photo._metadata.get(self.name, self.default))

    def __set__(self, photo, value):
        photo._metadata[self.name] = self._from_python(value)


class _IntMetadataProperty(_MetadataProperty):
    _to_python = int

class _DateMetadataProperty(_MetadataProperty):
    DATE_FORMAT = '%Y-%m-%d'

    def _from_python(self, value):
        if value is not None:
            return '-'.join(map(str, [value.year, value.month, value.day]))

    def _to_python(self, value):
        if value is not None:
            parts = map(int, value.split('-'))
            return datetime.date(*parts)

class _ListMetadataProperty(_MetadataProperty):
    """
    Very naive list serialization, uses pipe '|' separator with no escapes.
    """
    def __get__(self, photo, cls=None):
        value = super(_ListMetadataProperty, self).__get__(photo, cls)
        if value is not None:
            return map(self._to_python, value.split('|'))
        return []

    def __set__(self, photo, l):
        if l is not None:
            for item in l:
                if '|' in item:
                    raise ValueError(
                        "Pipe character '|' not allowed in list item.")
            value = '|'.join(l)
        else:
            value = []
        super(_ListMetadataProperty, self).__set__(photo, value)


class _ExifProperty(object):
    _to_python = lambda self, x: x

    def __init__(self, id):
        self.id = id

    def __get__(self, photo, cls=None):
        exif = getattr(photo, '_exif', None)
        if exif is None:
            exif = jpeg.getExif(photo.fpath)
            photo._exif = exif
        for tag in exif.exif:
            if tag.intID == self.id:
                return self._to_python(tag.value)

class _TimestampExifProperty(_ExifProperty):
    DATETIME_FORMAT = '%Y:%m:%d %H:%M:%S'

    def _to_python(self, value):
        return datetime.datetime.strptime(value, self.DATETIME_FORMAT)

def _as_bool(value):
    return value.lower() in ['true', 't', 'yes', 'y', '1']

class Photo(object):
    SW_VERSION = 1

    id = _MetadataProperty('id')
    version = _IntMetadataProperty('version', 0)
    title = _MetadataProperty('title')
    location = _MetadataProperty('location')
    photographer = _MetadataProperty('photographer')
    desc = _MetadataProperty('desc')
    visibility = _MetadataProperty('visibility', 'new')
    timestamp = _TimestampExifProperty(0x9003)
    date = _DateMetadataProperty('date')
    tags = _ListMetadataProperty('tags')

    def __init__(self, fpath):
        self.fpath = fpath
        self._metadata = Metadata(fpath)

        if self.date is None:
            t = self.timestamp
            if t is not None:
                self.date = datetime.date(t.year, t.month, t.day)

        self._evolve()

    def save(self):
        self._metadata.save()

    def _evolve(self):
        if self.version != self.SW_VERSION:
            for step in xrange(self.version + 1, self.SW_VERSION + 1):
                methodname = '_evolve%d' % step
                method = getattr(self, methodname)
                method()

    def _evolve1(self):
        metadata = self._metadata
        if 'published' in metadata:
            if _as_bool(metadata['published']):
                self.visibility = 'public'
            else:
                self.visibility = 'private'
            del metadata['published']

