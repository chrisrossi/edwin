from edwin.views.util import get_months

class TemplateAPI(object):

    def __init__(self, request):
        app_context = request.app_context
        self.templates = app_context.templates
        self.base_macro = self.templates['base.pt'].macros['base']
        self.application_url = request.application_url
        self.static_url = '%s/static/%s' % (
            self.application_url.rstrip('/'),
            app_context.static_version
        )
        self.user = request.remote_user
        self.logout_url = self.application_url.rstrip('/') + '/logout'
        self._request = request

    @property
    def months(self):
        return get_months(self._request, visibility=None)

