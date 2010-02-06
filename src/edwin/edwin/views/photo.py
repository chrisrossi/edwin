from dateutil.parser import parse as dateparse
import simplejson

from happy.acl import effective_principals
from happy.acl import has_permission
from happy.acl import require_permission
from happy.static import FileResponse
from happy.traversal import model_url

from edwin.views.api import TemplateAPI
from edwin.views.json import JSONResponse
from edwin.views.util import format_date

PHOTO_SIZE = (700, 700)

@require_permission('view')
def photo_view(request, photo):
    app_context = request.app_context
    images_route = app_context.routes['images']
    version = app_context.images.version(photo, PHOTO_SIZE)
    src = images_route.url(request, subpath=[version['fname'],])
    width, height = version['size']

    catalog = app_context.catalog
    siblings = list(catalog.photos(photo.__parent__,
                                   effective_principals(request)))
    index = 0
    n_siblings = len(siblings)
    for i in xrange(n_siblings):
        if siblings[i].id == photo.id:
            index = i
            break

    app_url = request.application_url.rstrip('/')
    prev_link = next_link = None
    if index > 0:
        prev_link = siblings[index-1].url(request)
    if index < n_siblings -1:
        next_link = siblings[index+1].url(request)
    back_link = model_url(request, photo.__parent__)

    ajax_url = model_url(request, photo, 'edit.json')

    return app_context.templates.render_to_response(
        'photo.pt',
        api=TemplateAPI(request),
        title=photo.title,
        location=photo.location,
        date=format_date(photo.date),
        desc=photo.desc,
        visibility=photo.visibility,
        src=src,
        width=width,
        height=height,
        prev_link=prev_link,
        next_link=next_link,
        back_link=back_link,
        download_link=model_url(request, photo, 'dl'),
        ajax_url=ajax_url,
        actions=simplejson.dumps(get_actions(photo, request)),
    )

def get_actions(photo, request):
    if not has_permission(request, 'edit', photo):
        return []

    actions = []
    if photo.visibility != 'public':
        actions.append(dict(name='publish', title='publish photo'))
    if photo.visibility != 'private':
        actions.append(dict(name='hide', title='hide photo'))
    return actions

def default_setter(photo, name, value):
    setattr(photo, name, value)
    return getattr(photo, name)

def date_setter(photo, name, value):
    try:
        if value.strip() == '':
            value = None
        if value is not None:
            value = dateparse(value).date()
        setattr(photo, name, value)
        ret_value = getattr(photo, name)
        if ret_value is None:
            return ''
        return format_date(ret_value)
    except ValueError:
        return 'Bad date format.'

setters = {
    'title': default_setter,
    'location': default_setter,
    'desc': default_setter,
    'date': date_setter,
}

def set_visibility(photo, request, visibility):
    photo.visibility = visibility
    photo.__parent__.update_acl()
    request.app_context.catalog.index(photo)
    return dict(visibility=photo.visibility)

def hide_photo(photo, request):
    return set_visibility(photo, request, 'private')

def publish_photo(photo, request):
    return set_visibility(photo, request, 'public')

actions = {
    'hide': hide_photo,
    'publish': publish_photo,
}

@require_permission('edit')
def edit_photo_view(request, photo):
    if 'action' in request.params:
        action = actions.get(request.params['action'], None)
        if action is not None:
            updated = action(photo, request)
            updated['actions'] = get_actions(photo, request)
            return JSONResponse(updated)

    updated = {}
    for name, value in request.params.items():
        if name not in setters:
            continue
        updated[name] = setters[name](photo, name, value)

    if 'date' in updated:
        album = photo.__parent__
        album.update_date_range()

    if updated:
        request.app_context.catalog.index(photo)

    return JSONResponse(updated)

@require_permission('view')
def download_photo_view(request, photo):
    response = FileResponse(photo.fpath)
    response.content_disposition = 'attachment; filename=%s' % photo.__name__
    return response
