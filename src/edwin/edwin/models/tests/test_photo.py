import unittest

class TestPhoto(unittest.TestCase):
    def setUp(self):
        import os
        import shutil
        import sys
        import tempfile
        here = os.path.dirname(sys.modules[__name__].__file__)
        tmpdir = tempfile.mkdtemp('_test', 'edwin_')
        for jpg in ['test.jpg', 'test2.jpg', 'test3.jpg']:
            src = os.path.join(here, jpg)
            dst = os.path.join(tmpdir, jpg)
            shutil.copy(src, dst)

        self.here = tmpdir
        self.fname = os.path.join(tmpdir, 'test.jpg')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.here)

    def test_metadata(self):
        from edwin.models.photo import Photo
        p = Photo(self.fname)
        p.photographer = 'Santa Clause'
        p.location = 'North Pole'
        p.title = 'Mrs. Clause and the elves'
        p.desc = 'Mrs. Clause and the elves blow off some steam.'
        self.assertEqual(p.version, 1)
        self.assertEqual(p.size, (3072, 2304))

        del p
        p = Photo(self.fname)
        self.assertEqual(p.photographer, 'Santa Clause')
        self.assertEqual(p.location, 'North Pole')
        self.assertEqual(p.title, 'Mrs. Clause and the elves')
        self.assertEqual(
            p.desc, 'Mrs. Clause and the elves blow off some steam.'
        )
        self.assertEqual(p.version, 1)

    def test_evolve1(self):
        from edwin.models.photo import Photo
        from edwin.models.metadata import OldMetadata
        import os
        metadata = OldMetadata(self.fname)

        p = Photo(self.fname)
        new_metadata = p._metadata._file
        p._metadata = metadata
        p._evolve()
        self.assertEqual(p.visibility, 'new')

        os.remove(new_metadata)
        metadata['published'] = True
        del metadata['version']
        metadata.save()
        p = Photo(self.fname)
        p._metadata = metadata
        p._evolve()
        self.assertEqual(p.visibility, 'public')

        os.remove(new_metadata)
        metadata['published'] = False
        del metadata['version']
        metadata.save()
        p = Photo(self.fname)
        p._metadata = metadata
        p._evolve()
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

        p = Photo(self.fname)
        self.assertEqual(p.date, expected)

    def test_guess_date_from_folder_name(self):
        import datetime
        import os
        import shutil
        from edwin.models.photo import Photo
        dirname = os.path.join(self.here, '2009', '12', '25.presents')
        os.makedirs(dirname)
        fname = os.path.join(dirname, 'test.jpg')
        shutil.copy(self.fname, fname)
        p = Photo(fname)
        self.assertEqual(p.date, datetime.date(2009, 12, 25))

    def test_tags(self):
        from edwin.models.photo import Photo
        p = Photo(self.fname)
        self.assertEqual(len(p.tags), 0)
        p.tags = ['foo', 'bar']

        p = Photo(self.fname)
        self.assertEqual(len(p.tags), 2)
        self.assertEqual(p.tags[0], 'foo')
        self.assertEqual(p.tags[1], 'bar')

    def test_remove_tags(self):
        from edwin.models.photo import Photo
        p = Photo(self.fname)
        self.assertEqual(len(p.tags), 0)
        p.tags = ['foo', 'bar']

        p = Photo(self.fname)
        self.assertEqual(len(p.tags), 2)
        self.assertEqual(p.tags[0], 'foo')
        self.assertEqual(p.tags[1], 'bar')

        p.tags = None

        p = Photo(self.fname)
        self.assertEqual(p.tags, [])

    def test_id(self):
        from edwin.models.photo import Photo
        p = Photo(self.fname)
        self.assertEqual(p.id, None)
        p.id = '1234567890'

        p = Photo(self.fname)
        self.assertEqual(p.id, '1234567890')

    def test_bad_timestamp(self):
        import os
        from edwin.models.photo import Photo
        p = Photo(os.path.join(self.here, 'test2.jpg'))
        self.assertEqual(p.date, None)

    def test_missing_exif(self):
        import os
        from edwin.models.photo import Photo
        p = Photo(os.path.join(self.here, 'test3.jpg'))
        self.assertEqual(p.date, None)

    def test_image(self):
        from edwin.models.photo import Photo
        p = Photo(self.fname)
        self.assertEqual(p.image.size, (3072, 2304))

    def test_rotate(self):
        from edwin.models.photo import Photo
        p = Photo(self.fname)
        self.assertEqual(p.size, (3072, 2304))

        p.rotate(90)
        self.assertEqual(p.size, (2304, 3072))
        self.assertEqual(p.image.size, (2304, 3072))

        p.rotate(270)
        self.assertEqual(p._rotation, 0)
        self.assertEqual(p.size, (3072, 2304))
        self.assertEqual(p.image.size, (3072, 2304))
