from happy.acl import require_permission
from happy.traversal import model_url

from edwin.views.api import TemplateAPI
from edwin.views.util import format_date_range
from edwin.views.util import format_month

@require_permission('view')
def month_view(request, year, month):
    app_context = request.app_context
    catalog = app_context.catalog
    albums = []
    for album in catalog.albums(
        month='%s-%s' % (year, month), visibility=None):
        albums.append(dict(
            title=album.title,
            url=album.url(request),
            date_range=format_date_range(album.date_range),
            )
        )

    return app_context.templates.render_to_response(
        'month.pt',
        api=TemplateAPI(request),
        albums=albums,
        date=format_month(int(year), int(month))
    )

