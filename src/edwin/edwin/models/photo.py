from edwin.models.metadata import Metadata

class _MetadataProperty(object):
    _to_python = lambda self, x: x

    def _from_python(self, value):
        if isinstance(value, basestring):
            return value
        return str(value)

    def __init__(self, name):
        self.name = name

    def __get__(self, photo, cls=None):
        return self._to_python(photo._metadata.get(self.name, None))

    def __set__(self, photo, value):
        photo._metadata[self.name] = self._from_python(value)


class _IntMetadataProperty(_MetadataProperty):
    _to_python = int


class Photo(object):
    SW_VERSION = 1

    title = _MetadataProperty('title')
    location = _MetadataProperty('location')
    photographer = _MetadataProperty('photographer')
    desc = _MetadataProperty('desc')
    version = _IntMetadataProperty('version')

    def __init__(self, fpath):
        self.fpath = fpath
        self._metadata = Metadata(fpath)

    def save(self):
        self._metadata.save()
