import unittest

class TestAlbum(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.path = tempfile.mkdtemp('_test', 'edwin_')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.path)

    def _make_one(self, test_photos=0):
        from edwin.models.album import Album
        return Album(self.path)

    def test_title(self):
        album = self._make_one()
        self.assertEqual(album.title, None)
        album.title = "Test Foo"

        album = self._make_one()
        self.assertEqual(album.title, "Test Foo")

    def test_desc(self):
        album = self._make_one()
        self.assertEqual(album.desc, None)
        album.desc = "Fooey"

        album = self._make_one()
        self.assertEqual(album.desc, "Fooey")
