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

    def __init__(self, root_path, connection_manager):
        self.root_path = root_path
        self._cursor = CursorContextFactory(connection_manager)

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

    def scan(self, album=None):
        if album is None:
            album = Album(self.root_path)
        with self._cursor() as c:
            for node in depthfirst(album):
                if isinstance(node, Photo):
                    self._index_photo(node, c)
                elif isinstance(node, Album):
                    if node.has_photos():
                        self._index_album(node, c)

    def album(self, path):
        with self._cursor() as c:
            c.execute(
                "select path, title, visibility, start_date, end_date, month "
                "from albums where path=?", (path,)
            )
            row = c.fetchone()
            if not row:
                raise KeyError(path)
            return AlbumBrain(self, *row)

    def photo(self, id):
        with self._cursor() as c:
            c.execute(
                "select path, modified, visibility, album_path, timestamp "
                "from photos where id=?", (id,)
            )
            row = c.fetchone()
            if not row:
                raise KeyError(id)
            return PhotoBrain(self, id, *row)

    def albums(self,
               visibility=None,
               start_date=None,
               end_date=None,
               month=None,
               limit=None):
        sql = ["select path, title, visibility, start_date, end_date, month "
               "from albums",]
        args = []
        constraints = []
        if visibility is not None:
            constraints.append('visibility=?')
            args.append(visibility)
        if start_date is not None:
            constraints.append('start_date >= ?')
            args.append(_serial_date(start_date))
        if end_date is not None:
            constraints.append('start_date < ?')
            args.append(_serial_date(end_date))
        if month is not None:
            start_date = month + '-01'
            y, m = map(int, month.split('-'))
            if m == 12:
                y += 1
                m = 1
            else:
                m += 1
            end_date = '%04d-%02d-01' % (y, m)
            constraints.append('start_date >= ?')
            args.append(start_date)
            constraints.append('start_date < ?')
            args.append(end_date)

        if constraints:
            sql.append('where')
            sql.append(' and '.join(constraints))

        sql.append('order by start_date desc')

        if limit is not None:
            sql.append('limit ?')
            args.append(limit)

        sql = ' '.join(sql)

        with self._cursor() as c:
            if args:
                c.execute(sql, args)
            else:
                c.execute(sql)

            for row in c:
                yield AlbumBrain(self, *row)

    def photos(self, album, visibility=None):
        sql = ("select id, path, modified, visibility, album_path, timestamp "
               "from photos where album_path=?")
        args = [self._relpath(album.path),]

        if visibility is not None:
            sql += " and visibility=?"
            args.append(visibility)
        sql += " order by timestamp asc, path asc"

        with self._cursor() as c:
            c.execute(sql, args)
            for row in c:
                yield PhotoBrain(self, *row)

    def months(self, visibility=None):
        with self._cursor() as c:
            sql = ['select distinct(month) from albums',]
            args = []
            if visibility is not None:
                sql.append('where visibility=?')
                args.append(visibility)
            sql.append('order by month desc')

            sql = ' '.join(sql)
            if args:
                c.execute(sql, args)
            else:
                c.execute(sql)
            return [row[0] for row in c]

    def _index_photo(self, photo, c):
        # Has photo been assigned id?
        if photo.id is None:
            photo.id = str(uuid.uuid1())

        else:
            # Delete previous record
            c.execute("delete from photos where id=?", (photo.id,))

        # Add to catalog
        path = self._relpath(photo.fpath)
        album_path = os.path.dirname(path)
        c.execute(
            "insert into photos (id, path, modified, visibility, "
            "album_path, timestamp) values(?,?,?,?,?,?)",
            (photo.id, path, photo.modified, photo.visibility, album_path,
             photo.timestamp)
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
        date_range = album.date_range
        if date_range is not None:
            start_date = _serial_date(date_range[0])
            end_date = _serial_date(date_range[1])
            month = start_date[:-3]
        else:
            start_date = end_date = month = None
        c.execute(
            "insert into albums (path, title, visibility, start_date, "
            "end_date, month) values (?, ?, ?, ?, ?, ?)",
            (album_path, album.title, visibility, start_date, end_date, month)
        )

    def _relpath(self, path):
        assert path.startswith(self.root_path), path
        return path[len(self.root_path):].strip('/')

class PhotoBrain(object):
    def __init__(self, catalog, id, path, modified, visibility, album_path,
                 timestamp):
        self.catalog = catalog
        self.id = id
        self.path = path
        self.modified = modified
        self.visibility = visibility
        self.album_path = album_path
        self.timestamp = timestamp

    def get(self):
        return Photo(os.path.join(self.catalog.root_path, self.path))

class AlbumBrain(object):
    def __init__(self, catalog, path, title, visibility, start_date, end_date,
                 month):
        self.catalog = catalog
        self.path = path
        self.title = title
        self.visibility = visibility
        if start_date is not None:
            self.date_range = (_parse_date(start_date), _parse_date(end_date))
        else:
            self.date_range = None
        self.month = month

    def get(self):
        return Album(os.path.join(self.catalog.root_path, self.path))

class CursorContextFactory(object):
    def __init__(self, connection_manager):
        self._manager = connection_manager

    @contextmanager
    def __call__(self):
        connection = self._manager.get_connection()
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except:
            connection.rollback()
            raise
        finally:
            cursor.close()
            self._manager.release_connection(connection)

def depthfirst(start):
    def visit(node):
        if hasattr(node, 'values'):
            for child in node.values():
                for value in visit(child):
                    yield value
        yield node
    return visit(start)

def _parse_date(value):
    if value is not None:
        parts = map(int, value.split('-'))
        return datetime.date(*parts)

def _serial_date(date):
    if date is not None:
        return '%04d-%02d-%02d' % (date.year, date.month, date.day)

init_sql = [
    "create table version (version int)",
    "insert into version (version) values (1)",

    "create table photos ("
    "    id text unique primary key,"
    "    path text,"
    "    modified real,"
    "    visibility text,"
    "    album_path text,"
    "    timestamp)",

    "create index photos_by_album_path on photos (album_path)",

    "create table albums ("
    "    path text unique primary key,"
    "    title text,"
    "    visibility text,"
    "    start_date text,"
    "    end_date text,"
    "    month text)",
]