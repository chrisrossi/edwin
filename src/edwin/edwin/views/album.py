from dateutil.parser import parse as dateparse

from happy.acl import effective_principals
from happy.acl import require_permission
from happy.traversal import model_url
from edwin.views.api import TemplateAPI
from edwin.views.json import JSONResponse
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
            src=images_route.url(request, fname=thumbnail['fname']),
            visibility=photo.visibility,
            )
        )

    months_route = app_context.routes['month']
    date = album.date_range[0]
    back_link = months_route.url(
        request, year=str(date.year), month='%02d' % date.month
    )

    return app_context.templates.render_to_response(
        'album.pt',
        api=TemplateAPI(request),
        title=album.title,
        location=album.location,
        desc=album.desc,
        date_range=format_date_range(album.date_range),
        date_range_edit=format_editable_date_range(album.date_range),
        photos=photos,
        back_link=back_link,
        actions={},
        ajax_url=model_url(request, album, 'edit.json'),
    )

EDITABLE_DATE_FORMAT = '%Y/%m/%d'
def format_editable_date_range(date_range):
    begin, end = date_range
    return '%s - %s' %(
        begin.strftime(EDITABLE_DATE_FORMAT),
        end.strftime(EDITABLE_DATE_FORMAT)
    )

def default_setter(album, name, value):
    setattr(album, name, value)
    return getattr(album, name)

def cascade_setter(album, name, value):
    ret_value = default_setter(album, name, value)
    for photo in album.photos():
        if not getattr(photo, name, None):
            setattr(photo, name, value)
    return ret_value

def date_range_setter(album, name, value):
    try:
        if value.strip() == '' or value is None:
            setattr(album, name, album._guess_date_range())
            return format_date_range(album.date_range)

        if '-' in value:
            begin, end = value.split('-')
        else:
            begin = end = value
        value = (dateparse(begin).date(), dateparse(end).date())

        setattr(album, name, value)
        return format_date_range(getattr(album, name))

    except ValueError:
        return 'Bad date format.'

def adjust_photo_dates(album):
    begin, end = album.date_range
    for photo in album.photos():
        if photo.date < begin:
            photo.date = begin
        elif photo.date > end:
            photo.date = end

setters = {
    'title': cascade_setter,
    'location': cascade_setter,
    'desc': default_setter,
    'date_range': date_range_setter,
}

@require_permission('view')
def edit_album_view(request, album):
    updated = {}
    for name, value in request.params.items():
        if name not in setters:
            continue
        updated[name] = setters[name](album, name, value)

    if 'date_range' in updated:
        adjust_photo_dates(album)

    if updated:
        request.app_context.catalog.index(album)

    return JSONResponse(updated)
