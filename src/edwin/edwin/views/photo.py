from dateutil.parser import parse as dateparse

from happy.static import FileResponse
from happy.traversal import model_url

from edwin.views.api import TemplateAPI
from edwin.views.json import JSONResponse
from edwin.views.util import format_date

PHOTO_SIZE = (700, 700)

def photo_view(request, photo):
    app_context = request.app_context
    images_route = app_context.routes['images']
    version = app_context.images.version(photo, PHOTO_SIZE)
    src = images_route.url(request, subpath=[version['fname'],])
    width, height = version['size']

    catalog = app_context.catalog
    siblings = list(catalog.photos(photo.__parent__, visibility='public'))
    index = 0
    n_siblings = len(siblings)
    for i in xrange(n_siblings):
        if siblings[i].id == photo.id:
            index = i
            break

    app_url = request.application_url.rstrip('/')
    prev_link = next_link = None
    if i > 0:
        prev_link = siblings[i-1].url(request)
    if i < n_siblings -1:
        next_link = siblings[i+1].url(request)
    back_link = model_url(request, photo.__parent__)

    ajax_url = model_url(request, photo, 'edit.json')

    return app_context.templates.render_to_response(
        'photo.pt',
        api=TemplateAPI(request),
        title=photo.title,
        location=photo.location,
        date=format_date(photo.date),
        desc=photo.desc,
        src=src,
        width=width,
        height=height,
        prev_link=prev_link,
        next_link=next_link,
        back_link=back_link,
        download_link=model_url(request, photo, 'dl'),
        ajax_url=ajax_url,
    )

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

def edit_photo_view(request, photo):
    updated = {}
    for name, value in request.params.items():
        if name not in setters:
            continue
        updated[name] = setters[name](photo, name, value)

    return JSONResponse(updated)

def download_photo_view(request, photo):
    response = FileResponse(photo.fpath)
    response.content_disposition = 'attachment; filename=%s' % photo.__name__
    return response
