from happy.acl import has_permission
from edwin.views.util import get_months
from edwin.views.util import get_new_albums

class TemplateAPI(object):

    def __init__(self, request):
        self._request = request

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
        self.load_jquery = self.may('edit')

    def months(self):
        return get_months(self._request)

    def may(self, permission):
        return has_permission(self._request, permission)

    def new_albums(self):
        return get_new_albums(self._request)
