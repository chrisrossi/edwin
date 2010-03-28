import unittest

class TestAlbum(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.path = tempfile.mkdtemp('_test', 'edwin_')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.path)

    def _make_photos(self, n, album=None):
        from edwin.models.photo import Photo
        import os
        import shutil
        import sys
        here = os.path.dirname(sys.modules[__name__].__file__)
        test_jpg = os.path.join(here, 'test.jpg')
        if album is None:
            album = self._make_one()
        for i in xrange(n):
            fpath = os.path.join(album.fspath, 'test%02d.jpg' % i)
            shutil.copy(test_jpg, fpath)
            photo = Photo(fpath)
            photo.title = 'Test %02d' % i

    def _make_subalbum(self, name, album):
        import os
        path = os.path.join(album.fspath, name)
        os.mkdir(path)
        return album[name]

    def _make_one(self):
        from edwin.models.album import Album
        return Album(self.path)

    def test_title(self):
        album = self._make_one()
        self.assertEqual(album.title, None)
        album.title = "Test Foo"
        self.assertEqual(album.title, "Test Foo")

        album = self._make_one()
        self.assertEqual(album.title, "Test Foo")

    def test_location(self):
        album = self._make_one()
        self.assertEqual(album.location, None)
        album.location = 'Greenland'
        self.assertEqual(album.location, 'Greenland')

        album = self._make_one()
        self.assertEqual(album.location, 'Greenland')

    def test_desc(self):
        album = self._make_one()
        self.assertEqual(album.desc, None)
        album.desc = "Fooey"
        self.assertEqual(album.desc, "Fooey")

        album = self._make_one()
        self.assertEqual(album.desc, "Fooey")
        album.desc = None
        self.assertEqual(album.desc, None)

        album = self._make_one()
        self.assertEqual(album.desc, None)

    def test_getphoto(self):
        self._make_photos(3)
        album = self._make_one()
        photo = album['test01.jpg']
        self.assertEqual(photo.title, 'Test 01')
        self.assertEqual(photo.__parent__, album)
        self.assertEqual(photo.__name__, 'test01.jpg')

    def test_getsubalbum(self):
        album = self._make_one()
        subalbum = self._make_subalbum('January', album)
        subalbum.title = 'Test January'

        album = self._make_one()
        self.assertEqual(album['January'].title, 'Test January')

    def test_keys(self):
        album = self._make_one()
        self._make_photos(2)
        self._make_subalbum('sub1', album)
        self._make_subalbum('sub2', album)

        album = self._make_one()
        expected = set(['test00.jpg', 'test01.jpg', 'sub1', 'sub2'])
        self.assertEqual(set(album.keys()), expected)

    def test_values(self):
        album = self._make_one()
        self._make_photos(2)
        self._make_subalbum('sub1', album).title = 'Sub 1'
        self._make_subalbum('sub2', album).title = 'Sub 2'

        album = self._make_one()
        expected = set(['Test 00', 'Test 01', 'Sub 1', 'Sub 2'])
        got = set([v.title for v in album.values()])
        self.assertEqual(got, expected)

    def test_photo_names(self):
        album = self._make_one()
        self._make_photos(2)
        self._make_subalbum('sub1', album)
        self._make_subalbum('sub2', album)

        album = self._make_one()
        expected = set(['test00.jpg', 'test01.jpg'])
        self.assertEqual(set(album.photo_names()), expected)

    def test_has_photos(self):
        album = self._make_one()
        self._make_photos(2)
        self._make_subalbum('sub1', album)

        album = self._make_one()
        self.failUnless(album.has_photos())
        self.failIf(album['sub1'].has_photos())

    def test_photos(self):
        album = self._make_one()
        self._make_photos(2)
        self._make_subalbum('sub1', album).title = 'Sub 1'
        self._make_subalbum('sub2', album).title = 'Sub 2'

        album = self._make_one()
        expected = set(['Test 00', 'Test 01'])
        got = set([v.title for v in album.photos()])
        self.assertEqual(got, expected)

    def test_guess_date_range_photos(self):
        from datetime import date
        album = self._make_one()
        self._make_photos(3)
        photo = album['test00.jpg']
        photo.date = date(2007, 8, 8)
        photo = album['test01.jpg']
        photo.date = date(2007, 9, 9)
        photo = album['test02.jpg']
        photo.date = date(2008, 7, 7)

        album = self._make_one()
        self.assertEqual(album.date_range,
                         (date(2007, 8, 8), date(2008, 7, 7)))

        photo = album['test02.jpg']
        photo.date = date(2007, 7, 7)
        self.assertEqual(album._guess_date_range(),
                         (date(2007, 7, 7), date(2007, 9, 9)))

    def test_guess_date_range_folders(self):
        from datetime import date
        album = self._make_one()
        sub1 = self._make_subalbum('sub1', album)
        sub1.date_range = date(2007, 1, 1), date(2007, 1, 31)
        sub2 = self._make_subalbum('sub2', album)
        sub2.date_range = date(2007, 1, 15), date(2007, 2, 15)
        sub3 = self._make_subalbum('sub3', album)
        sub3.date_range = date(2008, 1, 1), date(2008, 1, 1)

        album = self._make_one()
        self.assertEqual(album.date_range,
                         (date(2007, 1, 1), date(2008, 1, 1)))

    def test_acl(self):
        album = self._make_one()
        acl = [('foo', 'bar', ['baz', 'night'])]
        album._acl = acl
        self.assertEqual(album.__acl__, acl)

        album = self._make_one()
        self.assertEqual(album.__acl__, acl)

    def test_key_error(self):
        album = self._make_one()
        self.assertRaises(KeyError, album.__getitem__, 'foo')

