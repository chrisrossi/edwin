from happy.acl import effective_principals
from happy.acl import require_permission
from edwin.views.api import TemplateAPI
from edwin.views.util import format_date_range

@require_permission('view')
def homepage_view(request):
    catalog = request.app_context.catalog
    recent_albums = []
    for album in catalog.albums(effective_principals(request), limit=40):
        recent_albums.append(dict(
            title=album.title,
            url=album.url(request),
            date_range=format_date_range(album.date_range)
            )
        )

    return request.app_context.templates.render_to_response(
        'homepage.pt',
        api=TemplateAPI(request),
        recent_albums=recent_albums,
    )

