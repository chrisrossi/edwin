from chameleon.zpt.template import PageTemplateFile

import datetime
from edwin.config import ApplicationContext

from happy.routes import RoutesDispatcher
from happy.skin import Skin
from happy.skin import SkinApplication
from happy.sugar import wsgi_app
from happy.templates import Templates
from happy.traversal import TraversalDispatcher

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
        from edwin.views.album import album_view
        def root_factory(request):
            return app_context.photos
        albums = TraversalDispatcher(root_factory)
        albums.register(album_view, Album)

        self.responders = [
            subapps,
            routes,
            albums,
        ]

        app_context.routes = routes
        app_context.images = images

    def __call__(self, request):
        request = webob.Request(request.environ.copy())
        request.app_context = self.app_context
        for responder in self.responders:
            response = responder(request)
            if response is not None:
                break

        return response

def paste_app_factory(global_config, **config):
    app_config = global_config.copy()
    app_config.update(config)
    app_context = ApplicationContext(config=config)
    return wsgi_app(Application(app_context))

def make_app(config_file=None):
    from edwin.config import read_config
    return paste_app_factory({}, **read_config(config_file))

def main(args=sys.argv[1:]): #pragma NO COVERAGE, called from console
    from edwin.config import read_config
    config_file = None
    if args:
        config_file = args[0]
    config = read_config(config_file)
    app = paste_app_factory({}, **config)

    from paste.httpserver import server_runner
    port = config.get('http_port', 8080)
    server_runner(app, {}, port=port)
