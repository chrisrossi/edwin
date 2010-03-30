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

    def get_connection(self):
        return self._connection

    def release_connection(self, connection):
        pass

    def _make_repository(self, jpgs=['test.jpg', 'test2.jpg', 'test3.jpg'],
                         date=(2007,2,15), visibility='new'):
        import datetime
        import os
        import shutil
        import sys
        import tempfile
        from edwin.models.album import Album
        from edwin.models.photo import Photo
        self.root_path = tempfile.mkdtemp('_test', 'edwin_')
        here = os.path.dirname(sys.modules[__name__].__file__)
        test_jpgs = [os.path.join(here, jpg) for jpg in jpgs]
        n = len(test_jpgs)

        from happy.acl import Allow
        from happy.acl import Everyone
        Album(self.root_path)._acl = [
            (Allow, Everyone, 'view')
        ]

        if date is not None:
            year, month, day = 2007, 2, 15
        for album_name in ['one', 'two']:
            if date is not None:
                day += 1
            path = os.path.join(self.root_path, album_name)
            os.mkdir(path)
            album = Album(path)
            album.title = album_name.title()
            album.desc = 'Test %s' % album.title
            if date is not None:
                album.date_range = (
                    datetime.date(year, month, day),
                    datetime.date(year, month, day),
                    )
            for i in xrange(5):
                fpath = os.path.join(album.fspath, 'test%02d.jpg' % i)
                shutil.copy(test_jpgs[i%n], fpath)
                photo = Photo(fpath)
                photo.title = 'Test %02d' % i
                photo.visibility = visibility

    def _make_one(self):
        from edwin.models.catalog import Catalog
        return Catalog(self.root_path, self)

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
        self.assertEqual(
            brain.date_range,
            (datetime.date(2007, 2, 16), datetime.date(2007, 2, 16))
            )
        self.assertEqual(brain.get().desc, 'Test One')
        return catalog

    def test_unindex_album(self):
        catalog = self.test_index_album()
        album = catalog.album('one').get()
        catalog.unindex(album)
        self.assertRaises(KeyError, catalog.album, 'one')

    def test_index_album_no_date_range(self):
        import datetime
        self._make_repository(jpgs=['test2.jpg', 'test3.jpg'], date=None)
        catalog = self._make_one()
        root = self._get_root()
        catalog.index(root['one'])
        brain = catalog.album('one')
        self.assertEqual(brain.path, 'one')
        self.assertEqual(brain.title, 'One')
        self.assertEqual(brain.date_range, None)
        self.assertEqual(brain.get().desc, 'Test One')

    def test_index_photo(self):
        import datetime
        import os
        self._make_repository(jpgs=['test.jpg'])
        catalog = self._make_one()
        root = self._get_root()
        photo = root['one']['test02.jpg']
        catalog.index(photo)
        brain = catalog.photo(photo.id)
        self.assertEqual(brain.id, photo.id)
        self.assertEqual(brain.path, 'one/test02.jpg')
        self.assertEqual(brain.modified, os.path.getmtime(photo.fspath))
        self.assertEqual(brain.album_path, 'one')
        self.assertEqual(brain.get().title, 'Test 02')
        self.assertEqual(brain.size, (3072, 2304))

        brain = catalog.album('one')
        self.assertEqual(brain.path, 'one')
        self.assertEqual(brain.title, 'One')
        self.assertEqual(brain.date_range,
                         (datetime.date(2007, 2, 16),
                          datetime.date(2007, 2, 16))
                         )

        photo.rotate(90)
        catalog.index(photo)
        brain = catalog.photo(photo.id)
        self.assertEqual(brain.size, (2304, 3072))

    def test_unindex_photo(self):
        self._make_repository(jpgs=['test.jpg'])
        catalog = self._make_one()
        root = self._get_root()
        album = root['one']
        catalog.index(album['test01.jpg'])
        catalog.index(album['test02.jpg'])
        self.assertEqual(len(list(catalog.photos(album))), 2)

        catalog.unindex(album['test01.jpg'])
        self.assertEqual(len(list(catalog.photos(album))), 1)

        catalog.unindex(album['test02.jpg'])
        self.assertEqual(len(list(catalog.photos(album))), 0)
        self.assertRaises(KeyError, catalog.album, 'one')

    def test_albums(self):
        self._make_repository(jpgs=['test.jpg'])
        root = self._get_root()
        photo = root['one']['test03.jpg']
        photo.visibility = 'public'
        photo.__parent__.update_acl()

        catalog = self._make_one()
        catalog.scan()

        albums = list(catalog.albums())
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].title, 'Two')
        self.assertEqual(albums[1].title, 'One')

        from happy.acl import Everyone
        albums = list(catalog.albums([Everyone]))
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].title, 'One')

        albums = list(catalog.albums(['group.Administrators']))
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].title, 'Two')
        self.assertEqual(albums[1].title, 'One')

    def test_new_albums(self):
        self._make_repository(jpgs=['test.jpg'], visibility='private')
        root = self._get_root()
        photo = root['one']['test02.jpg']
        photo.visibility = 'public'
        photo.__parent__.update_acl()
        photo = root['one']['test03.jpg']
        photo.visibility = 'new'
        photo.__parent__.update_acl()

        catalog = self._make_one()
        catalog.scan()

        albums = list(catalog.new_albums())
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].title, 'One')

        photo = root['two']['test03.jpg']
        photo.visibility = 'new'
        photo.__parent__.update_acl()
        catalog.scan()

        albums = list(catalog.new_albums())
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].title, 'Two')
        self.assertEqual(albums[1].title, 'One')

        from happy.acl import Everyone
        albums = list(catalog.new_albums([Everyone]))
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].title, 'One')

        albums = list(catalog.new_albums(['group.Administrators']))
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].title, 'Two')
        self.assertEqual(albums[1].title, 'One')

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

    def test_albums_month(self):
        import datetime
        self._make_repository()
        root = self._get_root()
        catalog = self._make_one()
        catalog.scan()

        albums = list(catalog.albums(month='2007-02'))
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].title, 'Two')
        self.assertEqual(albums[1].title, 'One')

        root['one'].date_range = (
            datetime.date(2007, 12, 3),
            datetime.date(2007, 12, 15),
        )
        catalog.index(root['one'])

        albums = list(catalog.albums(month='2007-02'))
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].title, 'Two')

        albums = list(catalog.albums(month='2007-12'))
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].title, 'One')

    def test_photos(self):
        self._make_repository(jpgs=['test.jpg'])
        root = self._get_root()
        photo = root['one']['test03.jpg']
        photo.visibility = 'public'
        photo = root['one']['test01.jpg']
        photo.visibility = 'public'
        photo = root['one']['test02.jpg']
        photo.visibility = 'private'
        root['one'].update_acl()

        catalog = self._make_one()
        catalog.scan()

        photos = list(catalog.photos(root['one']))
        self.assertEqual(len(photos), 5)
        titles = [p.get().title for p in photos]
        self.assertEqual(titles, ['Test 00', 'Test 01', 'Test 02', 'Test 03',
                                  'Test 04'])

        from happy.acl import Everyone
        photos = list(catalog.photos(root['one'], [Everyone]))
        self.assertEqual(len(photos), 2)
        titles = [p.get().title for p in photos]
        self.assertEqual(titles, ['Test 01', 'Test 03'])

        photos = list(catalog.photos(root['one'], ['group.Administrators']))
        self.assertEqual(len(photos), 3)
        titles = [p.get().title for p in photos]
        self.assertEqual(titles, ['Test 00', 'Test 02', 'Test 04'])

    def test_months(self):
        from datetime import date
        self._make_repository(jpgs=['test.jpg'])
        root = self._get_root()
        root['two'].date_range = (
            date(2008, 3, 4),
            date(2008, 3, 5)
        )
        root['one']['test02.jpg'].visibility = 'public'
        root['one'].update_acl()

        catalog = self._make_one()
        catalog.scan()

        months = catalog.months()
        self.assertEqual(len(months), 2)
        self.assertEqual(months[0], '2008-03')
        self.assertEqual(months[1], '2007-02')

        from happy.acl import Everyone
        months = catalog.months([Everyone])
        self.assertEqual(len(months), 1)
        self.assertEqual(months[0], '2007-02')

        months = catalog.months(['group.Administrators'])
        self.assertEqual(len(months), 2)
        self.assertEqual(months[0], '2008-03')
        self.assertEqual(months[1], '2007-02')

    def test_months_filter_None(self):
        from datetime import date
        import os
        import pkg_resources
        self._make_repository(jpgs=['test.jpg'])
        root = self._get_root()
        three = os.path.join(root.fspath, 'three')
        os.mkdir(three)
        src = pkg_resources.resource_filename(
            'edwin.models.tests', 'test3.jpg')
        dst = os.path.join(three, 'test3.jpg')
        os.symlink(src, dst)
        catalog = self._make_one()
        catalog.scan()

        months = catalog.months()
        self.assertEqual(len(months), 1, months)
        self.assertEqual(months[0], '2007-02')

    def test_delete_photo(self):
        import os
        self._make_repository()
        catalog = self._make_one()
        catalog.scan()
        root = self._get_root()
        photo = root['one']['test01.jpg']
        photo_id = photo.id
        self.failIf(catalog.photo(photo_id) is None)
        os.remove(photo.fspath)
        catalog.scan()
        self.assertRaises(KeyError, catalog.photo, photo_id)

class TestCursorContextFactory(unittest.TestCase):
    def test_good(self):
        connection = DummyConnection()

        from edwin.models.catalog import CursorContextFactory
        factory = CursorContextFactory(DummyConnectionManager(connection))

        with factory() as cursor:
            self.assertEqual(cursor.state, 'created')

        self.assertEqual(connection.state, 'committed')
        self.failUnless(connection.released)
        self.failUnless(connection.closed)

    def test_bad(self):
        connection = DummyConnection()

        from edwin.models.catalog import CursorContextFactory
        factory = CursorContextFactory(DummyConnectionManager(connection))

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

class DummyConnectionManager(object):
    def __init__(self, c):
        self.c = c

    def get_connection(self):
        return self.c

    def release_connection(self, c):
        self.c.released = True
