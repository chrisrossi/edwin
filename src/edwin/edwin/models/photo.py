from edwin.models.metadata import Metadata

class _MetadataProperty(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, photo, cls=None):
        return photo._metadata.get(self.name, None)

    def __set__(self, photo, value):
        photo._metadata[self.name] = value


class Photo(object):
    title = _MetadataProperty('title')
    location = _MetadataProperty('location')
    photographer = _MetadataProperty('photographer')
    desc = _MetadataProperty('desc')

    def __init__(self, fpath):
        self.fpath = fpath
        self._metadata = Metadata(fpath)

    def save(self):
        self._metadata.save()
