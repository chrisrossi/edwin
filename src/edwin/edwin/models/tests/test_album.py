import unittest

class TestAlbum(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.path = tempfile.mkdtemp('_test', 'edwin_')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.path)

    def _make_photos(self, n):
        from edwin.models.photo import Photo
        import os
        import shutil
        import sys
        here = os.path.dirname(sys.modules[__name__].__file__)
        test_jpg = os.path.join(here, 'test.jpg')
        for i in xrange(n):
            fpath = os.path.join(self.path, 'test%02d.jpg' % i)
            shutil.copy(test_jpg, fpath)
            photo = Photo(fpath)
            photo.title = 'Test %02d' % i
            photo.save()

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

    def test_desc(self):
        album = self._make_one()
        self.assertEqual(album.desc, None)
        album.desc = "Fooey"
        self.assertEqual(album.desc, "Fooey")

        album = self._make_one()
        self.assertEqual(album.desc, "Fooey")

    def test_getitem(self):
        self._make_photos(3)
        album = self._make_one()
        photo = album['test01.jpg']
        self.assertEqual(photo.title, 'Test 01')
        self.assertEqual(photo.__parent__, album)
        self.assertEqual(photo.__name__, 'test01.jpg')
