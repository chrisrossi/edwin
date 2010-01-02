from happy.traversal import model_url

from edwin.views.api import TemplateAPI
from edwin.views.util import format_date

PHOTO_SIZE = (700, 700)

def photo_view(request, photo):
    app_context = request.app_context
    images_route = app_context.routes['images']
    version = app_context.images.version(photo, PHOTO_SIZE)
    src = images_route.url(request, subpath=[version['fname'],])
    width, height = version['size']

    #import pdb; pdb.set_trace()
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
        download_link=model_url(request, photo, 'dl')
    )
