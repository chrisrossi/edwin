from __future__ import with_statement
import os

_marker = object()

class _FSProperty(object):
    value = _marker

    def __init__(self, name):
        self.name = name

    def __get__(self, album, cls=None):
        if self.value is _marker:
            fpath = os.path.join(album.path, '.%s' % self.name)
            if os.path.exists(fpath):
                self.value = open(fpath).read()
            else:
                self.value = None
        return self.value

    def __set__(self, album, value):
        fpath = os.path.join(album.path, '.%s' % self.name)
        with open(fpath, 'w') as f:
            f.write(value)
        self.value = value

class Album(object):
    title = _FSProperty('title')
    desc = _FSProperty('desc')

    def __init__(self, path):
        self.path = path

