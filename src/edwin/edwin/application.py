from edwin.config import ApplicationContext

from happy.routes import RoutesDispatcher
from happy.sugar import wsgi_app

import sys
import webob


class Application(object):

    def __init__(self, app_context):
        self.app_context = app_context

        # Routes
        from edwin.views.home import homepage_view
        routes = RoutesDispatcher()
        routes.register(homepage_view, '/')

        self.responders = [
            routes,
        ]

    def __call__(self, request):
        request = webob.Request(request.environ.copy())
        request.app_context = self.app_context
        for responder in self.responders:
            response = responder(request)
            if response is not None:
                break

        return response


def make_app(global_config, **config):
    app_config = global_config.copy()
    app_config.update(config)
    app_context = ApplicationContext(config=config)
    return wsgi_app(Application(app_context))


def main(args=sys.argv[1:]):
    from edwin.config import read_config
    if args:
        config = read_config(args[0])
    else:
        config = read_config()

    app = make_app({}, *config)

    from paste.httpserver import server_runner
    port = config.get('http_port', 8080)
    server_runner(app, {}, port=port)
