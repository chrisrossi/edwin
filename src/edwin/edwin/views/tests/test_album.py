from edwin.views.tests.twillbase import TwillTest

import unittest

class AlbumViewTest(TwillTest):
    def test_it(self):
        from twill import commands as b
        b.follow('1975-11-04')
        b.find('1975-11-04')

class TestEditAlbumView(unittest.TestCase):
    def setUp(self):
        from edwin.views.album import edit_album_view
        self.fut = edit_album_view

        import os, sys
        import tempfile
        here = os.path.dirname(sys.modules[__name__].__file__)
        tmpdir = self.tmpdir = tempfile.mkdtemp('_edwin_test')
        src = os.path.join(here, 'test.jpg')
        dst = os.path.join(tmpdir, 'test1.jpg')
        os.symlink(src, dst)
        dst = os.path.join(tmpdir, 'test2.jpg')
        os.symlink(src, dst)

        from edwin.models.album import Album
        from happy.acl import Allow
        from happy.acl import Everyone
        self.album = album = Album(tmpdir)
        album._acl = [(Allow, Everyone, ['view', 'edit']),]

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_set_title(self):
        import simplejson
        self.album['test1.jpg'].title = 'Title'
        self.assertEqual(self.album.title, None)
        self.assertEqual(self.album['test2.jpg'].title, None)
        request = dummy_request('/', POST={
            'title': 'foo',
            'bad_title': 'foo',
        })
        request.context = self.album
        response = self.fut(request, self.album)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['title'], 'foo')
        self.assertEqual(self.album.title, 'foo')
        self.assertEqual(self.album['test1.jpg'].title, 'Title')
        self.assertEqual(self.album['test2.jpg'].title, 'foo')
        self.failIf('bad_title' in data)

        # Make sure title of photo follows subsequent changes when same as
        # album
        request = dummy_request('/', POST={
            'title': 'bar',
        })
        request.context = self.album
        response = self.fut(request, self.album)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['title'], 'bar')
        self.assertEqual(self.album.title, 'bar')
        self.assertEqual(self.album['test1.jpg'].title, 'Title')
        self.assertEqual(self.album['test2.jpg'].title, 'bar')

    def test_set_location(self):
        import simplejson
        self.album['test1.jpg'].location = 'Location'
        self.assertEqual(self.album.location, None)
        self.assertEqual(self.album['test2.jpg'].location, None)
        request = dummy_request('/', POST={
            'location': 'foo',
        })
        request.context = self.album
        response = self.fut(request, self.album)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['location'], 'foo')
        self.assertEqual(self.album.location, 'foo')
        self.assertEqual(self.album['test1.jpg'].location, 'Location')
        self.assertEqual(self.album['test2.jpg'].location, 'foo')

    def test_set_desc(self):
        import simplejson
        self.assertEqual(self.album.desc, None)
        request = dummy_request('/', POST={
            'desc': 'foo',
        })
        request.context = self.album
        response = self.fut(request, self.album)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['desc'], 'foo')
        self.assertEqual(self.album.desc, 'foo')
        self.assertEqual(self.album['test1.jpg'].desc, None)
        self.assertEqual(self.album['test2.jpg'].desc, None)

    def test_set_date_later(self):
        import datetime
        import simplejson
        self.assertEqual(self.album.date_range, (datetime.date(2008, 12, 4),
                                                 datetime.date(2008, 12, 4)))
        request = dummy_request('/', POST={
            'date_range': '7/7/1975',
        })
        request.context = self.album
        response = self.fut(request, self.album)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['date_range'], 'July 7, 1975')
        self.assertEqual(self.album.date_range, (datetime.date(1975, 7, 7),
                                                 datetime.date(1975, 7, 7)))
        self.assertEqual(self.album['test1.jpg'].date,
                         datetime.date(1975, 7, 7))
        self.assertEqual(self.album['test2.jpg'].date,
                         datetime.date(1975, 7, 7))

    def test_set_date_adjust_photo_dates(self):
        import datetime
        import simplejson
        self.album['test1.jpg'].date = datetime.date(1970, 3, 4)
        self.assertEqual(self.album.date_range, (datetime.date(2008, 12, 4),
                                                 datetime.date(2008, 12, 4)))
        request = dummy_request('/', POST={
            'date_range': '7/7/1975',
        })
        request.context = self.album
        response = self.fut(request, self.album)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['date_range'], 'July 7, 1975')
        self.assertEqual(self.album.date_range, (datetime.date(1975, 7, 7),
                                                 datetime.date(1975, 7, 7)))
        self.assertEqual(self.album['test1.jpg'].date,
                         datetime.date(1975, 7, 7))
        self.assertEqual(self.album['test2.jpg'].date,
                         datetime.date(1975, 7, 7))

    def test_set_date_range(self):
        import datetime
        import simplejson
        self.assertEqual(self.album.date_range, (datetime.date(2008, 12, 4),
                                                 datetime.date(2008, 12, 4)))
        request = dummy_request('/', POST={
            'date_range': '2008/12/4 - 2008/12/5',
        })
        request.context = self.album
        response = self.fut(request, self.album)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['date_range'], 'December 4-5, 2008')
        self.assertEqual(self.album.date_range, (datetime.date(2008, 12, 4),
                                                 datetime.date(2008, 12, 5)))
        self.assertEqual(self.album['test1.jpg'].date,
                         datetime.date(2008, 12, 4))
        self.assertEqual(self.album['test2.jpg'].date,
                         datetime.date(2008, 12, 4))

    def test_set_date_recalculate_date_range(self):
        import datetime
        import simplejson
        self.album['test1.jpg'].date = datetime.date(1970, 3, 4)
        self.album['test2.jpg'].date = datetime.date(1970, 3, 6)
        self.assertEqual(self.album.date_range, (datetime.date(2008, 12, 4),
                                                 datetime.date(2008, 12, 4)))
        request = dummy_request('/', POST={
            'date_range': '',
        })
        request.context = self.album
        response = self.fut(request, self.album)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['date_range'], 'March 4-6, 1970')
        self.assertEqual(self.album.date_range, (datetime.date(1970, 3, 4),
                                                 datetime.date(1970, 3, 6)))
        self.assertEqual(self.album['test1.jpg'].date,
                         datetime.date(1970, 3, 4))
        self.assertEqual(self.album['test2.jpg'].date,
                         datetime.date(1970, 3, 6))

    def test_set_bad_date(self):
        import datetime
        import simplejson
        self.assertEqual(self.album.date_range, (datetime.date(2008, 12, 4),
                                                 datetime.date(2008, 12, 4)))
        request = dummy_request('/', POST={
            'date_range': 'foo',
        })
        request.context = self.album
        response = self.fut(request, self.album)
        self.assertEqual(response.status_int, 200)
        data = simplejson.loads(response.body)
        self.assertEqual(data['date_range'], 'Bad date format.')
        self.assertEqual(self.album.date_range, (datetime.date(2008, 12, 4),
                                                 datetime.date(2008, 12, 4)))

def dummy_request(*args, **kw):
    import webob
    request = webob.Request.blank(*args, **kw)
    request.app_context = DummyApplicationContext()
    request.authenticated_principals = ['group.Administrators']
    return request

class DummyApplicationContext(object):
    def __init__(self):
        self.catalog = DummyCatalog()
        self.routes = DummyRoutes()
        self.images = DummyImageApplication()

class DummyRoutes(object):
    def __getitem__(self, name):
        return self

    def url(self, request, fname, subpath):
        return 'http://example.com/images/%s' % fname

class DummyImageApplication(object):
    def __init__(self):
        self.cleared_cache = []

    def version(self, photo, req_size):
        return {
            'fname': 'test.%dx%d.jpg' % req_size,
            'size': (200, 300)
        }

    def clear_cache(self, photo=None):
        self.cleared_cache.append(photo)

class DummyCatalog(object):
    def __init__(self):
        self.indexed = []
        self.unindexed = []

    def index(self, obj):
        self.indexed.append(obj)

    def unindex(self, obj):
        self.unindexed.append(obj)
