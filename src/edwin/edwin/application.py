from chameleon.zpt.template import PageTemplateFile

import datetime
from edwin.config import ApplicationContext
from happy.acl import ALL_PERMISSIONS
from happy.acl import Allow
from happy.acl import Deny
from happy.acl import Everyone
from happy.routes import RoutesDispatcher
from happy.skin import Skin
from happy.skin import SkinApplication
from happy.sugar import wsgi_app
from happy.templates import Templates
from happy.traversal import TraversalDispatcher

import os
import sys
import time
import webob


class Application(object):

    def __init__(self, app_context):
        self.app_context = app_context

        # Set up skin
        static_version = str(int(time.time()))
        static = SkinApplication(
            Skin('edwin.views:static'),
            expires_timedelta=datetime.timedelta(days=3650)
        )
        templates = Templates(Skin('edwin.views:templates'), PageTemplateFile)
        app_context.static_version = static_version
        app_context.templates = templates

        subapps = RoutesDispatcher(rewrite_paths=True)
        subapps.register(static, 'static', '/static/%s/*' % static_version)

        # Image application (serves images and creates sizes)
        from edwin.views.image import ImageApplication
        images = ImageApplication(app_context.image_cache_dir)

        # Routes
        from edwin.views.home import homepage_view
        from edwin.views.month import month_view
        routes = RoutesDispatcher()
        routes.register(homepage_view, 'homepage', '/')
        routes.register(month_view, 'month', '/archive/:year/:month/')
        routes.register(images, 'images', '/image/*')

        # Use traversal for albums and photos
        from edwin.models.album import Album
        from edwin.models.photo import Photo
        from edwin.views.album import album_view
        from edwin.views.photo import photo_view
        from edwin.views.photo import edit_photo_view
        from edwin.views.photo import download_photo_view
        def root_factory(request):
            return app_context.photos
        photos = TraversalDispatcher(root_factory)
        photos.register(album_view, Album)
        photos.register(photo_view, Photo)
        photos.register(edit_photo_view, Photo, 'edit.json')
        photos.register(download_photo_view, Photo, 'dl')
        self.responders = [
            subapps,
            routes,
            photos,
        ]

        app_context.routes = routes
        app_context.images = images

    def __call__(self, request):
        request = webob.Request(request.environ.copy())
        request.app_context = self.app_context
        request.context = self.app_context.photos # overridden by traversal
        for responder in self.responders:
            response = responder(request)
            if response is not None:
                break

        return response

def login_middleware(app, config_file=None):
    from happy.login import FormLoginMiddleware
    from happy.login import HtpasswdBroker
    from happy.login import FlatFilePrincipalsBroker
    from happy.login import RandomUUIDCredentialBroker
    from edwin.config import read_config
    if config_file is None:
        from edwin.config import get_default_config_file
        config_file = get_default_config_file()
    config = read_config(config_file, 'login')
    here = os.path.dirname(config_file)
    htpasswd_file = config.get('htpasswd_file', os.path.join(here, 'htpasswd'))
    principals_file = config.get('principals_file',
                                 os.path.join(here, 'principals'))
    credentials_file = config.get('credentials_file',
                                  os.path.join(here, 'credentials.db'))
    return FormLoginMiddleware(
        app,
        HtpasswdBroker(htpasswd_file),
        FlatFilePrincipalsBroker(principals_file),
        RandomUUIDCredentialBroker(credentials_file),
    )

import time
def timeit(app):
    def middleware(request):
        start = time.time()
        response = app(request)
        if response is not None and response.content_type == 'text/html':
            elapsed = time.time() - start
            rps = 1.0 / elapsed
            print "Requests Per Second: %0.2f\t%s" % (rps, request.path_info)
        return response
    return middleware

def make_app(config_file=None):
    from edwin.config import read_config
    config = {}
    if config_file is not None and os.path.exists(config_file):
        config = read_config(config_file)
    app = Application(ApplicationContext(config=config))
    app = login_middleware(app)
    app = timeit(app)
    return wsgi_app(app)

def main(args=sys.argv[1:]): #pragma NO COVERAGE, called from console
    from edwin.config import read_config
    config_file = None
    if args:
        config_file = args[0]
    app = make_app(config_file)

    from paste.httpserver import server_runner
    config = read_config(config_file)
    port = config.get('http_port', 8080)
    server_runner(app, {}, port=port)

def profile(): #pragma NO COVERAGE
    import cProfile
    cProfile.run("from edwin.application import main; main()")
