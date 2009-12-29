from __future__ import with_statement

from contextlib import contextmanager
class Catalog(object):
    SW_VERSION = 1

    _version = None

    def __init__(self, connection_factory, release_connection):
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

init_sql = [
    "create table version (version int)",
    "insert into version (version) values (1)",
]