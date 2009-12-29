import unittest

class TestCatalog(unittest.TestCase):
    root_path = None

    def setUp(self):
        import sqlite3
        self._connection = sqlite3.connect(':memory:')

    def tearDown(self):
        if self.root_path is not None:
            import shutil
            shutil.rmtree(self.root_path)

    def _get_connection(self):
        return self._connection

    def _release_connection(self, connection):
        pass

    def _make_repository(self):
        import datetime
        import os
        import shutil
        import sys
        import tempfile
        from edwin.models.album import Album
        from edwin.models.photo import Photo
        self.root_path = tempfile.mkdtemp('_test', 'edwin_')
        here = os.path.dirname(sys.modules[__name__].__file__)
        test_jpg = os.path.join(here, 'test.jpg')

        year, month, day = 2007, 2, 15
        for album_name in ['one', 'two']:
            day += 1
            path = os.path.join(self.root_path, album_name)
            os.mkdir(path)
            album = Album(path)
            album.title = album_name.title()
            album.desc = 'Test %s' % album.title
            album.date_range = (
                datetime.date(year, month, day),
                datetime.date(year, month, day),
                )
            for i in xrange(5):
                fpath = os.path.join(album.path, 'test%02d.jpg' % i)
                shutil.copy(test_jpg, fpath)
                photo = Photo(fpath)
                photo.title = 'Test %02d' % i
                photo.save()

    def _make_one(self):
        from edwin.models.catalog import Catalog
        return Catalog(self.root_path,
                       self._get_connection, self._release_connection)

    def _get_root(self):
        from edwin.models.album import Album
        return Album(self.root_path)

    def test_version(self):
        catalog = self._make_one()
        self.assertEqual(catalog.version, 1)

    def test_get_photo_keyerror(self):
        catalog = self._make_one()
        self.assertRaises(KeyError, catalog.photo, 'foo')

    def test_get_album_keyerror(self):
        catalog = self._make_one()
        self.assertRaises(KeyError, catalog.album, 'foo')

    def test_index_album(self):
        import datetime
        self._make_repository()
        catalog = self._make_one()
        root = self._get_root()
        catalog.index(root['one'])
        brain = catalog.album('one')
        self.assertEqual(brain.path, 'one')
        self.assertEqual(brain.title, 'One')
        self.assertEqual(brain.visibility, 'private')
        self.assertEqual(
            brain.date_range,
            (datetime.date(2007, 2, 16), datetime.date(2007, 2, 16))
            )
        self.assertEqual(brain.get().desc, 'Test One')

    def test_index_photo(self):
        import datetime
        import os
        self._make_repository()
        catalog = self._make_one()
        root = self._get_root()
        photo = root['one']['test02.jpg']
        catalog.index(photo)
        brain = catalog.photo(photo.id)
        self.assertEqual(brain.id, photo.id)
        self.assertEqual(brain.path, 'one/test02.jpg')
        self.assertEqual(brain.modified, os.path.getmtime(photo.fpath))
        self.assertEqual(brain.visibility, 'new')
        self.assertEqual(brain.album_path, 'one')
        self.assertEqual(brain.get().title, 'Test 02')

        brain = catalog.album('one')
        self.assertEqual(brain.path, 'one')
        self.assertEqual(brain.title, 'One')
        self.assertEqual(brain.visibility, 'private')
        self.assertEqual(brain.date_range,
                         (datetime.date(2007, 2, 16),
                          datetime.date(2007, 2, 16))
                         )

    def test_make_photo_visible(self):
        self.test_index_photo()
        catalog = self._make_one()
        root = self._get_root()
        photo = root['one']['test02.jpg']
        photo.visibility = 'public'
        photo.save()
        catalog.index(photo)

        brain = catalog.photo(photo.id)
        self.assertEqual(brain.visibility, 'public')

        brain = catalog.album('one')
        self.assertEqual(brain.visibility, 'public')

    def test_albums(self):
        self._make_repository()
        root = self._get_root()
        photo = root['one']['test03.jpg']
        photo.visibility = 'public'
        photo.save()

        catalog = self._make_one()
        catalog.scan()

        albums = list(catalog.albums())
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].title, 'Two')
        self.assertEqual(albums[1].title, 'One')

        albums = list(catalog.albums('public'))
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].title, 'One')

        albums = list(catalog.albums('private'))
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].title, 'Two')

    def test_albums_by_date(self):
        import datetime
        self._make_repository()
        root = self._get_root()
        catalog = self._make_one()
        catalog.scan()

        albums = list(catalog.albums(
            start_date=datetime.date(2007, 2, 16),
            end_date=datetime.date(2007, 2, 17)
        ))

        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].title, 'One')

    def test_albums_limit(self):
        self._make_repository()
        root = self._get_root()
        catalog = self._make_one()
        catalog.scan()

        albums = list(catalog.albums(limit=1))
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].title, 'Two')


    def test_photos(self):
        self._make_repository()
        root = self._get_root()
        photo = root['one']['test03.jpg']
        photo.visibility = 'public'
        photo.save()
        photo = root['one']['test01.jpg']
        photo.visibility = 'public'
        photo.save()
        photo = root['one']['test02.jpg']
        photo.visibility = 'private'
        photo.save()

        catalog = self._make_one()
        catalog.scan()

        photos = list(catalog.photos(root['one']))
        self.assertEqual(len(photos), 5)
        titles = [p.get().title for p in photos]
        self.assertEqual(titles, ['Test 00', 'Test 01', 'Test 02', 'Test 03',
                                  'Test 04'])

        photos = list(catalog.photos(root['one'], 'new'))
        self.assertEqual(len(photos), 2)
        titles = [p.get().title for p in photos]
        self.assertEqual(titles, ['Test 00', 'Test 04'])

        photos = list(catalog.photos(root['one'], 'public'))
        self.assertEqual(len(photos), 2)
        titles = [p.get().title for p in photos]
        self.assertEqual(titles, ['Test 01', 'Test 03'])

        photos = list(catalog.photos(root['one'], 'private'))
        self.assertEqual(len(photos), 1)
        titles = [p.get().title for p in photos]
        self.assertEqual(titles, ['Test 02',])

    def test_months(self):
        self._make_repository()
        catalog = self._make_one()
        catalog.scan()
        months = catalog.months()
        self.assertEqual(len(months), 1)
        self.assertEqual(months[0], '2007-02')

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
