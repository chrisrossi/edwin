import unittest

class TestTrash(unittest.TestCase):
    def setUp(self):
        import os
        import shutil
        import sys
        import tempfile
        from edwin.models.album import Album
        from edwin.models.photo import Photo

        self.path = path = tempfile.mkdtemp('_test', 'edwin_')
        here = os.path.dirname(sys.modules[__name__].__file__)
        test_jpg = os.path.join(here, 'test.jpg')
        dst = os.path.join(path, 'test.jpg')
        os.symlink(test_jpg, dst)
        photo = Photo(dst)
        photo.title = 'Test Foo'

        self.album = Album(path)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.path)

    def _make_one(self):
        from edwin.models.trash import Trash
        trash = Trash()
        trash.__parent__ = self.album
        return trash

    def test_trash_unknown_type(self):
        trash = self._make_one()
        self.assertRaises(ValueError, trash.trash, object())

    def test_trash_photo(self):
        self.failUnless('test.jpg' in self.album)
        self.assertEqual(self.album['test.jpg'].title, 'Test Foo')

        album = self.album
        trash = self._make_one()
        trash_id = trash.trash(album['test.jpg'])
        self.failIf('test.jpg' in album)

        self.assertEqual(trash.restore(trash_id).title, 'Test Foo')
        self.failUnless('test.jpg' in album)
        self.assertEqual(album['test.jpg'].title, 'Test Foo')

    def test_trash_transformed_photo(self):
        self.failUnless('test.jpg' in self.album)
        self.assertEqual(self.album['test.jpg'].title, 'Test Foo')
        self.album['test.jpg'].rotate(90)
        self.assertEqual(self.album['test.jpg'].size, (2304, 3072))

        album = self.album
        trash = self._make_one()
        trash_id = trash.trash(album['test.jpg'])
        self.failIf('test.jpg' in album)

        self.assertEqual(trash.restore(trash_id).title, 'Test Foo')
        self.failUnless('test.jpg' in album)
        self.assertEqual(album['test.jpg'].title, 'Test Foo')
        self.assertEqual(self.album['test.jpg'].size, (2304, 3072))
