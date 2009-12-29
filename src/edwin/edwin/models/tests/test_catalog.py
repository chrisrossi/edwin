import unittest

class TestCatalog(unittest.TestCase):
    def setUp(self):
        import sqlite3
        self._connection = sqlite3.connect(':memory:')

    def _get_connection(self):
        return self._connection

    def _release_connection(self, connection):
        pass

    def _make_one(self):
        from edwin.models.catalog import Catalog
        return Catalog(self._get_connection, self._release_connection)

    def test_version(self):
        catalog = self._make_one()
        self.assertEqual(catalog.version, 1)

class TestCursorContextFactory(unittest.TestCase):
    def test_good(self):
        connection = DummyConnection()
        def get_connection():
            return connection
        def release_connection(c):
            c.released = True

        from edwin.models.catalog import CursorContextFactory
        factory = CursorContextFactory(get_connection, release_connection)

        with factory() as cursor:
            self.assertEqual(cursor.state, 'created')

        self.assertEqual(connection.state, 'committed')
        self.failUnless(connection.released)
        self.failUnless(connection.closed)

    def test_bad(self):
        connection = DummyConnection()
        def get_connection():
            return connection
        def release_connection(c):
            c.released = True

        from edwin.models.catalog import CursorContextFactory
        factory = CursorContextFactory(get_connection, release_connection)

        try:
            with factory() as cursor:
                raise NameError('Jackson')
            self.fail() #pragma NO COVERAGE, should be unreachable
        except NameError:
            pass

        self.assertEqual(connection.state, 'aborted')
        self.failUnless(connection.released)
        self.failUnless(connection.closed)

class DummyConnection(object):
    state = 'created'
    closed = False
    released = False

    def cursor(self):
        return self

    def commit(self):
        self.state = 'committed'

    def rollback(self):
        self.state = 'aborted'

    def close(self):
        self.closed = True
