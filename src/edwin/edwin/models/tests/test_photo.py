import unittest

class TestPhoto(unittest.TestCase):
    def setUp(self):
        import os
        import sys
        import tempfile
        here = os.path.dirname(sys.modules[__name__].__file__)
        fd, fname = tempfile.mkstemp('.jpg', 'edwin-test')
        f = os.fdopen(fd, 'wb')
        f.write(open(os.path.join(here, 'test.jpg')).read())
        f.close()

        self.fname = fname

    def tearDown(self):
        import os
        os.remove(self.fname)

    def test_metadata(self):
        from edwin.models.photo import Photo
        p = Photo(self.fname)
        p.photographer = 'Santa Clause'
        p.location = 'North Pole'
        p.title = 'Mrs. Clause and the elves'
        p.desc = 'Mrs. Clause and the elves blow off some steam.'
        p.version = 2
        p.save()

        del p
        p = Photo(self.fname)
        self.assertEqual(p.photographer, 'Santa Clause')
        self.assertEqual(p.location, 'North Pole')
        self.assertEqual(p.title, 'Mrs. Clause and the elves')
        self.assertEqual(
            p.desc, 'Mrs. Clause and the elves blow off some steam.'
        )
        self.assertEqual(p.version, 2)

    def test_evolve1(self):
        from edwin.models.photo import Photo
        p = Photo(self.fname)
        self.assertEqual(p.visibility, 'new')
        p._metadata['published'] = True
        p.save()

        p = Photo(self.fname)
        self.assertEqual(p.visibility, 'public')

        p._metadata['published'] = False
        p.save()

        p = Photo(self.fname)
        self.assertEqual(p.visibility, 'private')
