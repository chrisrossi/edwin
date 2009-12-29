from __future__ import with_statement

from contextlib import contextmanager
import datetime

from edwin.models.album import Album
from edwin.models.photo import Photo

import os
import uuid

class Catalog(object):
    SW_VERSION = 1

    _version = None

    def __init__(self, root_path, connection_factory, release_connection):
        self.root_path = root_path
        self._cursor = CursorContextFactory(
            connection_factory, release_connection
        )

        with self._cursor() as c:
            c.execute(
                "select count(*) from sqlite_master where type='table' and "
                "name='version'"
            )
            if c.fetchone()[0] == 0:
                for line in init_sql:
                    c.execute(line)

    @property
    def version(self):
        if self._version is None:
            with self._cursor() as c:
                c.execute("select version from version")
                self._version = c.fetchone()[0]

        return self._version

    def index(self, obj):
        with self._cursor() as c:
            if isinstance(obj, Photo):
                self._index_photo(obj, c)

                # Reindex album while we're at it, since changes in photo
                # visibility impact albu visibility.
                self._index_album(Album(os.path.dirname(obj.fpath)), c)

            elif isinstance(obj, Album):
                self._index_album(obj, c)

    def album(self, path):
        with self._cursor() as c:
            c.execute(
                "select path, title, visibility, date from albums "
                "where path=?", (path,)
            )
            row = c.fetchone()
            if not row:
                raise KeyError(path)
            return AlbumBrain(self, *row)

    def photo(self, id):
        with self._cursor() as c:
            c.execute(
                "select path, modified, visibility, album_path from photos "
                "where id=?", (id,)
            )
            row = c.fetchone()
            if not row:
                raise KeyError(id)
            return PhotoBrain(self, id, *row)

    def _index_photo(self, photo, c):
        # Has photo been assigned id?
        if photo.id is None:
            photo.id = uuid.uuid1()
            photo.save()

        else:
            # Delete previous record
            c.execute("delete from photos where id=?", (photo.id,))

        # Add to catalog
        path = self._relpath(photo.fpath)
        album_path = os.path.dirname(path)
        c.execute(
            "insert into photos (id, path, modified, visibility, "
            "album_path) values(?,?,?,?,?)",
            (photo.id, path, photo.modified, photo.visibility, album_path)
        )

    def _index_album(self, album, c):
        album_path = self._relpath(album.path)

        # Delete previous record
        c.execute("delete from albums where path=?", (album_path,))

        # Calculate visibility
        c.execute("select distinct(visibility) from photos where album_path=?",
                  (album_path,))
        visibilities = set([row[0] for row in c])
        if 'public' in visibilities:
            visibility = 'public'
        else:
            visibility = 'private'

        # Update record
        c.execute(
            "insert into albums (path, title, visibility, date) values "
            "(?, ?, ?, ?)", (album_path, album.title, visibility,
                             _serial_date(album.date_range[0]))
        )

    def _relpath(self, path):
        assert path.startswith(self.root_path), path
        return path[len(self.root_path):].strip('/')

class PhotoBrain(object):
    def __init__(self, catalog, id, path, modified, visibility, album_path):
        self.catalog = catalog
        self.id = id
        self.path = path
        self.modified = modified
        self.visibility = visibility
        self.album_path = album_path

    def get(self):
        return Photo(os.path.join(self.catalog.root_path, self.path))

class AlbumBrain(object):
    def __init__(self, catalog, path, title, visibility, date):
        self.catalog = catalog
        self.path = path
        self.title = title
        self.visibility = visibility
        self.date = _parse_date(date)

    def get(self):
        return Album(os.path.join(self.catalog.root_path, self.path))

class CursorContextFactory(object):
    def __init__(self, get_connection, release_connection):
        self.get_connection = get_connection
        self.release_connection = release_connection

    @contextmanager
    def __call__(self):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except:
            connection.rollback()
            raise
        finally:
            cursor.close()
            self.release_connection(connection)

def _parse_date(value):
    parts = map(int, value.split('-'))
    return datetime.date(*parts)

def _serial_date(date):
    return '%04d-%02d-%02d' % (date.year, date.month, date.day)

init_sql = [
    "create table version (version int)",
    "insert into version (version) values (1)",

    "create table photos ("
    "    id text unique primary key,"
    "    path text,"
    "    modified real,"
    "    visibility text,"
    "    album_path text)",

    "create index photos_by_album_path on photos (album_path)",

    "create table albums ("
    "    path text unique primary key,"
    "    title text,"
    "    visibility text,"
    "    date text)",
]