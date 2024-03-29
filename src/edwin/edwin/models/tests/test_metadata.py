import unittest

class OldMetadataTests(unittest.TestCase):
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

    def test_it(self):
        from edwin.models.metadata import OldMetadata as Metadata
        m = Metadata(self.fname)
        self.assertEqual(len(m), 0)

        m['foo'] = 'bar'
        m['hello'] = 'howdy'
        self.assertEqual(len(m), 2)
        self.assertEqual(m['foo'], 'bar')
        self.assertEqual(m['hello'], 'howdy')
        m.save()

        del m
        m = Metadata(self.fname)
        self.assertEqual(len(m), 3)
        self.assertEqual(m['foo'], 'bar')
        self.assertEqual(m['hello'], 'howdy')
        self.assertEqual(m['published'], 'False')

        m['foo'] = 'baz'
        m['hanky'] = 'panky'
        self.assertEqual(len(m), 4)
        self.assertEqual(m['foo'], 'baz')
        self.assertEqual(m['hello'], 'howdy')
        self.assertEqual(m['hanky'], 'panky')
        self.assertEqual(m['published'], 'False')
        m.save()

        del m
        m = Metadata(self.fname)
        self.assertEqual(len(m), 4)
        self.assertEqual(m['foo'], 'baz')
        self.assertEqual(m['hello'], 'howdy')
        self.assertEqual(m['hanky'], 'panky')
        self.assertEqual(m['published'], 'False')

class MetadataTests(unittest.TestCase):
    def setUp(self):
        import os
        import shutil
        import sys
        import tempfile
        here = os.path.dirname(sys.modules[__name__].__file__)
        tmpdir = tempfile.mkdtemp('_test', 'edwin_')
        src = os.path.join(here, 'test.jpg')
        dst = os.path.join(tmpdir, 'test.jpg')
        shutil.copy(src, dst)

        self.fname = dst
        self.tmpdir = tmpdir

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_it(self):
        from edwin.models.metadata import Metadata
        m = Metadata(self.fname)
        self.assertEqual(len(m), 0)

        m['foo'] = 'bar'
        m['hello'] = 'howdy'
        self.assertEqual(len(m), 2)
        self.assertEqual(m['foo'], 'bar')
        self.assertEqual(m['hello'], 'howdy')

        del m
        m = Metadata(self.fname)
        self.assertEqual(len(m), 2)
        self.assertEqual(m['foo'], 'bar')
        self.assertEqual(m['hello'], 'howdy')

        m['foo'] = 'baz'
        m['hanky'] = 'panky'
        self.assertEqual(len(m), 3)
        self.assertEqual(m['foo'], 'baz')
        self.assertEqual(m['hello'], 'howdy')
        self.assertEqual(m['hanky'], 'panky')

        del m
        m = Metadata(self.fname)
        self.assertEqual(len(m), 3)
        self.assertEqual(m['foo'], 'baz')
        self.assertEqual(m['hello'], 'howdy')
        self.assertEqual(m['hanky'], 'panky')
