from ConfigParser import ConfigParser
import os
import sqlite3
import sys
import threading

from edwin.models.album import Album
from edwin.models.catalog import Catalog

class ApplicationContext(object):
    def __init__(self, config_file=None, config=None, connection_manager=None):
        # read config
        if config_file is None:
            config_file = get_default_config_file()
        all_config = read_config(config_file)
        if config is not None:
            all_config.update(config)

        # set up application resources
        db_file = all_config.get('db_file', get_default_db_file())
        photos_dir = all_config.get('photos_dir', get_default_photos_dir())

        if connection_manager is None:
            connection_manager = ThreadedConnectionManager(db_file)

        for dirname in (os.path.dirname(db_file), photos_dir):
            if not os.path.exists(dirname):
                os.makedirs(dirname)

        self.catalog = Catalog(photos_dir, connection_manager)
        self.photos = Album(photos_dir)
        self.config = all_config
        self.db_file = db_file
        self.photos_dir = photos_dir
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

def _here():
    here = sys.argv[0]
    here = os.path.abspath(os.path.normpath(here))
    return os.path.dirname(os.path.dirname(here))

def get_default_config_file():
    return os.path.join(_here(), 'etc', 'edwin.ini')

def get_default_db_file():
    return os.path.join(_here(), 'var', 'photos.catalog')

def get_default_photos_dir():
    return os.path.join(_here(), 'var', 'photos')

def read_config(path, section="edwin"):
    config = {}
    parser = ConfigParser()
    parser.read([path,])
    for k, v in parser.items('DEFAULT'):
        config[k] = v
    for k, v in parser.items(section):
        config[k] = v
    return config