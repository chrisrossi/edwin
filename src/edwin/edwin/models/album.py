from __future__ import with_statement
import os

from edwin.models.photo import Photo

class _FSProperty(object):

    def __init__(self, name):
        self.name = name

    def __get__(self, album, cls=None):
        fpath = os.path.join(album.path, '.%s' % self.name)
        if os.path.exists(fpath):
            return open(fpath).read()

    def __set__(self, album, value):
        fpath = os.path.join(album.path, '.%s' % self.name)
        with open(fpath, 'w') as f:
            f.write(value)

class Album(object):
    title = _FSProperty('title')
    desc = _FSProperty('desc')

    def __init__(self, path):
        self.path = path

    def __getitem__(self, fname):
        fpath = os.path.join(self.path, fname)
        if os.path.isfile(fpath):
            photo = Photo(fpath)
            photo.__name__ = fname
            photo.__parent__ = self
            return photo
