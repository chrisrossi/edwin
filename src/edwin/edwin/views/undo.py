from happy.traversal import model_url
from edwin.utils import find_trash
from webob.exc import HTTPFound

def undo_view(request, code):
    if not code.startswith('trash:'):
        return None

    # XXX Need security here.  Probably need to add api to trash to be able
    # to retrieve context(s) involved for purposes of security checking, before
    # performing undo operation.
    trash_id = code[6:]
    trash = find_trash(request.context)
    restored = trash.restore(trash_id, request.app_context.catalog)
    response = HTTPFound(location=model_url(request, restored))
    response.set_cookie('undo', '')
    return response
