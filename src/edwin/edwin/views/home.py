from edwin.views.api import TemplateAPI
from edwin.views.util import format_date_range

def homepage_view(request):
    catalog = request.app_context.catalog
    app_url = request.application_url.rstrip('/')
    recent_albums = []
    for album in catalog.albums(visibility=None, limit=10):
        recent_albums.append(dict(
            title=album.title,
            url='%s/%s' % (app_url, album.path),
            date_range=format_date_range(album.date_range)
            )
        )

    return request.app_context.templates.render_to_response(
        'homepage.pt',
        api=TemplateAPI(request),
        recent_albums=recent_albums,
    )

