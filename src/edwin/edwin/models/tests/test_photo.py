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

    def test_timestamp(self):
        import datetime
        from edwin.models.photo import Photo
        p = Photo(self.fname)
        expected = datetime.datetime(2008, 12, 4, 22, 42, 57)
        self.assertEqual(p.timestamp, expected)

        expected = datetime.date(2008, 12, 4)
        self.assertEqual(p.date, expected)

        expected = datetime.date(1975, 7, 7)
        p.date = expected
        p.save()

        p = Photo(self.fname)
        self.assertEqual(p.date, expected)

    def test_tags(self):
        from edwin.models.photo import Photo
        p = Photo(self.fname)
        self.assertEqual(len(p.tags), 0)
        p.tags = ['foo', 'bar']
        p.save()

        p = Photo(self.fname)
        self.assertEqual(len(p.tags), 2)
        self.assertEqual(p.tags[0], 'foo')
        self.assertEqual(p.tags[1], 'bar')

    def test_bad_tag(self):
        from edwin.models.photo import Photo
        p = Photo(self.fname)
        self.assertRaises(ValueError, setattr, p, 'tags', ['foo|bar'])

    def test_remove_tags(self):
        from edwin.models.photo import Photo
        p = Photo(self.fname)
        self.assertEqual(len(p.tags), 0)
        p.tags = ['foo', 'bar']
        p.save()

        p = Photo(self.fname)
        self.assertEqual(len(p.tags), 2)
        self.assertEqual(p.tags[0], 'foo')
        self.assertEqual(p.tags[1], 'bar')

        p.tags = None
        p.save()

        p = Photo(self.fname)
        self.assertEqual(p.tags, [])

    def test_id(self):
        from edwin.models.photo import Photo
        p = Photo(self.fname)
        self.assertEqual(p.id, None)
        p.id = '1234567890'
        p.save()

        p = Photo(self.fname)
        self.assertEqual(p.id, '1234567890')
