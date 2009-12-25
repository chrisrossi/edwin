import unittest

class MetadataTests(unittest.TestCase):
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
        from edwin.models.metadata import Metadata
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
        self.assertEqual(len(m), 2)
        self.assertEqual(m['foo'], 'bar')
        self.assertEqual(m['hello'], 'howdy')

        m['foo'] = 'baz'
        m['hanky'] = 'panky'
        self.assertEqual(len(m), 3)
        self.assertEqual(m['foo'], 'baz')
        self.assertEqual(m['hello'], 'howdy')
        self.assertEqual(m['hanky'], 'panky')
        m.save()

        del m
        m = Metadata(self.fname)
        self.assertEqual(len(m), 3)
        self.assertEqual(m['foo'], 'baz')
        self.assertEqual(m['hello'], 'howdy')
        self.assertEqual(m['hanky'], 'panky')
