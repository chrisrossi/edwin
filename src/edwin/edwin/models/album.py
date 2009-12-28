from __future__ import with_statement
import os

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

