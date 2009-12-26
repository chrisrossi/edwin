from edwin.models.metadata import Metadata

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

def _as_bool(value):
    return value.lower() in ['true', 't', 'yes', 'y', '1']

class Photo(object):
    SW_VERSION = 1

    version = _IntMetadataProperty('version', 0)
    title = _MetadataProperty('title')
    location = _MetadataProperty('location')
    photographer = _MetadataProperty('photographer')
    desc = _MetadataProperty('desc')
    visibility = _MetadataProperty('visibility', 'new')

    def __init__(self, fpath):
        self.fpath = fpath
        self._metadata = Metadata(fpath)

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
            del self._metadata['published']

