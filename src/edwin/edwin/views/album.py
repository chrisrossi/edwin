from happy.acl import effective_principals
from happy.acl import require_permission
from happy.traversal import model_url
from edwin.views.api import TemplateAPI
from edwin.views.util import format_date_range

THUMBNAIL_SIZE = (100, 100)

@require_permission('view')
def album_view(request, album):
    app_context = request.app_context
    catalog = app_context.catalog
    images = app_context.images
    images_route = app_context.routes['images']
    photos = []
    for photo in catalog.photos(album, effective_principals(request)):
        thumbnail = images.version(photo, THUMBNAIL_SIZE)
        photos.append(dict(
            url=photo.url(request),
            thumb=thumbnail,
            src=images_route.url(request, subpath=[thumbnail['fname'],]),
            )
        )

    months_route = app_context.routes['month']
    date = album.date_range[0]
    back_link = months_route.url(
        request, dict(year=str(date.year), month='%02d' % date.month)
    )

    return app_context.templates.render_to_response(
        'album.pt',
        api=TemplateAPI(request),
        title=album.title,
        desc=album.desc,
        date_range=format_date_range(album.date_range),
        photos=photos,
        back_link=back_link,
    )
