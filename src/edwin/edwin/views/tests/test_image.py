import unittest

class TestImageApplication(unittest.TestCase):
    def setUp(self):
        import os
        import sys
        import tempfile
        here = os.path.dirname(sys.modules[__name__].__file__)
        test_jpg = os.path.join(here, 'test.jpg')

        self.tmpdir = tempfile.mkdtemp('_edwin_test')
        self.photo_file = os.path.join(self.tmpdir, 'test.jpg')
        os.symlink(test_jpg, self.photo_file)


    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_it(self):
        from edwin.models.photo import Photo
        photo = Photo(self.photo_file)
        photo.id = '123456'

        from happy.acl import Allow
        from happy.acl import Everyone
        photo.__acl__ = [(Allow, Everyone, ['view']),]

        from edwin.views.image import ImageApplication
        app = ImageApplication(self.tmpdir)

        version = app.version(photo, (300, 300))
        self.assertEqual(version['fname'], '123456.300x300.jpg')
        self.assertEqual(version['size'], (300, 225))

        import os
        import webob
        cache_file = os.path.join(self.tmpdir, '123456.300x300.jpg')
        request = webob.Request.blank('/image/123456.300x300.jpg')
        request.app_context = DummyAppContextCatalog(photo)
        response = app(request)
        self.assertEqual(response.content_type, 'image/jpeg')

        import Image
        image = Image.open(cache_file)
        self.assertEqual(image.size, (300, 225))

    def test_unauthorized(self):
        from edwin.models.photo import Photo
        photo = Photo(self.photo_file)
        photo.id = '123456'

        from happy.acl import Allow
        from happy.acl import Everyone

        from edwin.views.image import ImageApplication
        app = ImageApplication(self.tmpdir)

        import os
        import webob
        request = webob.Request.blank('/image/123456.300x300.jpg')
        request.app_context = DummyAppContextCatalog(photo)
        response = app(request)
        self.assertEqual(response.status_int, 401)

    def test_forbidden(self):
        from edwin.models.photo import Photo
        photo = Photo(self.photo_file)
        photo.id = '123456'

        from happy.acl import Allow
        from happy.acl import Everyone

        from edwin.views.image import ImageApplication
        app = ImageApplication(self.tmpdir)

        import os
        import webob
        request = webob.Request.blank('/image/123456.300x300.jpg')
        request.app_context = DummyAppContextCatalog(photo)
        request.remote_user = 'chris'
        response = app(request)
        self.assertEqual(response.status_int, 403)

    def test_dont_scale_up(self):
        from edwin.models.photo import Photo
        photo = Photo(self.photo_file)
        photo.id = '123456'

        from edwin.views.image import ImageApplication
        app = ImageApplication(self.tmpdir)

        version = app.version(photo, (6000, 6000))
        self.assertEqual(version['size'], (3072, 2304))

    def test_scale_by_height(self):
        from edwin.models.photo import Photo
        photo = Photo(self.photo_file)
        photo.id = '123456'

        from edwin.views.image import ImageApplication
        app = ImageApplication(self.tmpdir)

        version = app.version(photo, (3000, 300))
        self.assertEqual(version['size'], (400, 300))


class DummyAppContextCatalog(object):
    def __init__(self, photo):
        self._photo = photo

    @property
    def catalog(self):
        return self

    def photo(self, id):
        return self

    def get(self):
        return self._photo
