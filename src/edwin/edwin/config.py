from ConfigParser import ConfigParser
import os
import sqlite3
import sys
import threading

from edwin.models.album import Album
from edwin.models.catalog import Catalog

here = os.path.dirname(os.path.dirname(
    os.path.abspath(os.path.normpath(sys.argv[0]))
))


class ApplicationContext(object):
    def __init__(self, config_file=None, config=None, connection_manager=None):
        # read config
        if config_file is None:
            config_file = get_default_config_file()
        all_config = {}
        if config_file is not None and os.path.exists(config_file):
            all_config = read_config(config_file)
        if config is not None:
            all_config.update(config)

        # set up application resources
        db_file = all_config.get('db_file', get_default_db_file())
        db_file = os.path.abspath(os.path.normpath(db_file))
        photos_dir = all_config.get('photos_dir', get_default_photos_dir())
        photos_dir = os.path.abspath(os.path.normpath(photos_dir))
        if connection_manager is None:
            connection_manager = ThreadedConnectionManager(db_file)
        image_cache_dir = all_config.get('image_cache_dir',
                                         get_default_image_cache_dir())
        image_cache_dir = os.path.abspath(os.path.normpath(image_cache_dir))

        self.catalog = Catalog(photos_dir, connection_manager)
        self.photos = Album(photos_dir)
        self.config = all_config
        self.db_file = db_file
        self.photos_dir = photos_dir
        self.image_cache_dir = image_cache_dir
        self.connection_manager = connection_manager

class ThreadedConnectionManager(object):
    def __init__(self, db_file):
        self._connections = threading.local()
        self._db_file = db_file

    def get_connection(self):
        connection = getattr(self._connections, 'connection', None)
        if connection is None:
            connection = sqlite3.connect(self._db_file)
            self._connections.connection = connection
        return connection

    def release_connection(self, connection):
        assert connection is self._connections.connection
        del self._connections.connection



def get_default_config_file():
    return os.path.join(here, 'etc', 'edwin.ini')

def get_default_db_file():
    return os.path.join(here, 'var', 'photos.catalog')

def get_default_photos_dir():
    return os.path.join(here, 'var', 'photos')

def get_default_image_cache_dir():
    return os.path.join(here, 'var', 'cached_images')

def read_config(path=None, section="edwin"):
    if path is None:
        path = get_default_config_file() #pragma NO COVERAGE
    here = os.path.dirname(path)
    config = {}
    parser = ConfigParser({'here': here})
    parser.read([path,])
    for k, v in parser.items('DEFAULT'):
        config[k] = v
    for k, v in parser.items(section):
        config[k] = v
    return config