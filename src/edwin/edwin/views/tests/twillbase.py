import unittest

class TwillTest(unittest.TestCase):
    """
    Base class for twill tests.
    """

    start_date = (1975, 7, 7)
    n_albums = 20
    delta_days = 8
    n_photos = 10
    initial_visibility = 'public'

    def setUp(self):
        # Create test fixtures
        import os
        import shutil
        import sys
        import tempfile
        tmpdir = tempfile.mkdtemp('edwin_', '_twill_test_fixture')
        here = os.path.dirname(sys.modules[__name__].__file__)
        test_jpg = os.path.join(here, 'test.jpg')
        photos_dir = os.path.join(tmpdir, 'var', 'photos')

        import datetime
        from edwin.models.album import Album
        from edwin.models.photo import Photo
        date = datetime.date(*self.start_date)

        from happy.acl import ALL_PERMISSIONS
        from happy.acl import Allow
        from happy.acl import Everyone
        os.makedirs(photos_dir)
        Album(photos_dir)._acl = [
            (Allow, Everyone, ['view']),
            (Allow, 'group.Administrators', ALL_PERMISSIONS),
        ]

        for i in xrange(self.n_albums):
            parts = map(str, (date.year, date.month, date.day))
            album_dir = os.path.join(photos_dir, *parts)
            os.makedirs(album_dir)
            album = Album(album_dir)
            album.title = str(date)

            for j in xrange(self.n_photos):
                photo_file = os.path.join(album_dir, 'photo_%02d.jpg' % j)
                os.symlink(test_jpg, photo_file)
                photo = Photo(photo_file)
                photo.title = 'Test %d' % j
                photo.visibility = self.initial_visibility

            album.update_acl()
            date += datetime.timedelta(days=self.delta_days)

        etc = os.path.join(tmpdir, 'etc')
        os.mkdir(etc)
        for fname in ('test.ini', 'htpasswd', 'principals'):
            src = os.path.join(here, fname)
            dst = os.path.join(etc, fname)
            os.symlink(src, dst)

        ini_file = os.path.join(etc, 'test.ini')
        from edwin.config import ApplicationContext
        app_context = ApplicationContext(ini_file)
        app_context.catalog.scan()

        # Twill is unable to parse the standard login form.  I don't know why.
        # I don't want to fuck with it any more.  Substitute this very easy
        # to parse one.
        def login_template(**kw):
            return u"""
                <html>
                  <head>
                    <title>WTF?</title>
                  </head>
                  <body>
                    <form method="POST" name="login">
                      <input type="hidden" name="redirect_to"
                             value="%(redirect_to)s">
                      <input name="login" value="%(login)s">
                      <input name="password" type="password">
                      <input type="submit" value="log in">
                      %(status_msg)s
                    </form>
                  </body>
                </html>
            """ % kw

        # Init wsgi app
        from edwin.application import make_app
        app = make_app(ini_file, login_template=login_template)
        def get_app():
            return app

        # Register wsgi intercept and visit homepage to start off
        import twill
        twill.add_wsgi_intercept('localhost', 8080, get_app)
        twill.commands.go('http://localhost:8080/')
        twill.commands.code(200)

        self.tmpdir = tmpdir

    def login(self):
        from twill import commands as b
        b.go('/login')
        b.fv('login', 'login', 'chris')
        b.fv('login', 'password', 'chris')
        b.submit()

        b.find('You are logged in as chris.')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)
