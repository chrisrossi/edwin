from edwin.views.tests.twillbase import TwillTest
import unittest

class TestPhotoView(TwillTest):
    def test_it(self):
        from twill import commands as b
        b.follow('1975-11-04')
        b.find('1975-11-04')
        b.follow('photo_02.jpg')
        b.find('Test 2')
        b.find('November 04, 1975')
        b.follow('download')
        b.code(200)

class TestEditPhotoView(unittest.TestCase):
    def setUp(self):
        from edwin.views.photo import edit_photo_view
        self.fut = edit_photo_view

        import os, sys
        import tempfile
        here = os.path.dirname(sys.modules[__name__].__file__)
        tmpdir = self.tmpdir = tempfile.mkdtemp('_edwin_test')
        src = os.path.join(here, 'test.jpg')
        dst = os.path.join(tmpdir, 'test.jpg')
        os.symlink(src, dst)

        from edwin.models.album import Album
        from happy.acl import Allow
        from happy.acl import Everyone
        album = Album(tmpdir)
        album._acl = [(Allow, Everyone, ['view', 'edit']),]
        self.photo = album['test.jpg']

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_set_title(self):
        import simplejson
        self.assertEqual(self.photo.title, None)
        request = dummy_request('/', POST={
            'title': 'foo',
            'bad_title': 'foo',
        })
        request.context = self.photo
        response = self.fut(request, self.photo)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['title'], 'foo')
        self.assertEqual(self.photo.title, 'foo')
        self.failIf('bad_title' in data)

    def test_set_location(self):
        import simplejson
        self.assertEqual(self.photo.location, None)
        request = dummy_request('/', POST={
            'location': 'foo',
        })
        request.context = self.photo
        response = self.fut(request, self.photo)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['location'], 'foo')
        self.assertEqual(self.photo.location, 'foo')

    def test_set_desc(self):
        import simplejson
        self.assertEqual(self.photo.desc, None)
        request = dummy_request('/', POST={
            'desc': 'foo',
        })
        request.context = self.photo
        response = self.fut(request, self.photo)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['desc'], 'foo')
        self.assertEqual(self.photo.desc, 'foo')

    def test_set_date(self):
        import datetime
        import simplejson
        self.assertEqual(self.photo.date, datetime.date(2008, 12, 4))
        request = dummy_request('/', POST={
            'date': '7/7/1975',
        })
        request.context = self.photo
        response = self.fut(request, self.photo)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['date'], 'July 07, 1975')
        self.assertEqual(self.photo.date, datetime.date(1975, 7, 7))

    def test_set_blank_date(self):
        import datetime
        import simplejson
        self.assertEqual(self.photo.date, datetime.date(2008, 12, 4))
        request = dummy_request('/', POST={
            'date': '',
        })
        request.context = self.photo
        response = self.fut(request, self.photo)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['date'], '')
        self.assertEqual(self.photo.date, None)

    def test_set_bad_date(self):
        import datetime
        import simplejson
        self.assertEqual(self.photo.date, datetime.date(2008, 12, 4))
        request = dummy_request('/', POST={
            'date': 'foo',
        })
        request.context = self.photo
        response = self.fut(request, self.photo)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['date'], 'Bad date format.')
        self.assertEqual(self.photo.date, datetime.date(2008, 12, 4))

    def test_date_updates_album_date_range(self):
        import datetime
        request = dummy_request('/', POST={
            'date': '7/7/1975',
        })
        request.context = self.photo

        album = self.photo.__parent__
        self.fut(request, self.photo)
        self.assertEqual(album.date_range,
                         (datetime.date(1975, 7, 7),
                          datetime.date(1975, 7, 7))
                         )

        album.date_range = (datetime.date(1975, 7, 1),
                            datetime.date(1975, 7, 1))
        self.fut(request, self.photo)
        self.assertEqual(album.date_range,
                         (datetime.date(1975, 7, 7),
                          datetime.date(1975, 7, 7))
                         )

        album.date_range = (datetime.date(1975, 7, 1),
                            datetime.date(1975, 7, 10))
        self.fut(request, self.photo)
        self.assertEqual(album.date_range,
                         (datetime.date(1975, 7, 1),
                          datetime.date(1975, 7, 10))
                         )

    def test_hide_photo(self):
        self.assertEqual(self.photo.visibility, 'new')
        request = dummy_request('/', POST={
            'action': 'hide',
        })
        request.context = self.photo
        self.fut(request, self.photo)
        self.assertEqual(self.photo.visibility, 'private')

    def test_publish_photo(self):
        self.assertEqual(self.photo.visibility, 'new')
        request = dummy_request('/', POST={
            'action': 'publish',
        })
        request.context = self.photo
        self.fut(request, self.photo)
        self.assertEqual(self.photo.visibility, 'public')

def dummy_request(*args, **kw):
    import webob
    request = webob.Request.blank(*args, **kw)
    request.app_context = DummyApplicationContext()
    return request

class DummyApplicationContext(object):
    def __init__(self):
        self.catalog = DummyCatalog()

class DummyCatalog(object):
    def __init__(self):
        self.indexed = []

    def index(self, obj):
        self.indexed.append(obj)
