import datetime
from dateutil.parser import parse as dateparse

from happy.acl import effective_principals
from happy.acl import has_permission
from happy.acl import require_permission
from happy.traversal import model_url
from edwin.views.api import TemplateAPI
from edwin.views.json import JSONResponse
from edwin.views.util import format_date_range

THUMBNAIL_SIZE = (100, 100)

@require_permission('view')
def album_view(request, album):
    app_context = request.app_context
    months_route = app_context.routes['month']
    if album.date_range is not None:
        date = album.date_range[0]
        back_link = months_route.url(
            request, year=str(date.year), month='%02d' % date.month
        )
    else:
        back_link = ''
    photos = _get_photos(request, album)

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
        actions=get_actions(request, album, photos),
        ajax_url=model_url(request, album, 'edit.json'),
    )

def _get_photos(request, album):
    app_context = request.app_context
    catalog = app_context.catalog
    images = app_context.images
    images_route = app_context.routes['images']
    photos = []
    for photo in catalog.photos(album, effective_principals(request)):
        thumbnail = images.version(photo, THUMBNAIL_SIZE)
        photos.append(dict(
            id=photo.id,
            url=photo.url(request),
            thumb=thumbnail,
            src=images_route.url(request, fname=thumbnail['fname']),
            visibility=photo.visibility,
            )
        )

    return photos

def get_actions(request, album, photos):
    if not has_permission(request, 'edit', album):
        return []

    actions = []
    visibilities = set()
    for photo in photos:
        visibilities.add(photo['visibility'])

    if len(visibilities) == 1:
        visibility = iter(visibilities).next()
        if visibility != 'public':
            actions.append(dict(name='publish_all',
                                title='publish all photos'))
        if visibility != 'private':
            actions.append(dict(name='hide_all',
                                title='hide all photos'))

    else:
        actions.append(dict(name='publish_all',
                            title='publish all photos'))
        actions.append(dict(name='hide_all',
                            title='hide all photos'))
        if 'new' in visibilities:
            actions.append(dict(name='publish_new',
                                title='publish new photos'))
            actions.append(dict(name='hide_new',
                                title='hide new photos'))
            if 'public' in visibilities:
                actions.append(dict(name='hide_public',
                                    title='hide public photos'))
            if 'private' in visibilities:
                actions.append(dict(name='publish_hidden',
                                    title='publish hidden photos'))

    return actions

def _set_visibility(request, album, from_, to):
    photos = []
    for photo in album.photos():
        if from_ is None or photo.visibility == from_:
            photo.visibility = to
            photos.append(photo)

    catalog = request.app_context.catalog
    if from_ is not None:
        discriminator = lambda p: p.visibility == from_
    else:
        discriminator = None
    catalog.index_album_and_photos(album, photos)

    photos = _get_photos(request, album)
    return dict(
        actions=get_actions(request, album, photos),
        photos=photos
    )

def publish_all(request, album):
    return _set_visibility(request, album, None, 'public')

def hide_all(request, album):
    return _set_visibility(request, album, None, 'private')

def publish_new(request, album):
    return _set_visibility(request, album, 'new', 'public')

def publish_hidden(request, album):
    return _set_visibility(request, album, 'private', 'public')

def hide_new(request, album):
    return _set_visibility(request, album, 'new', 'private')

def hide_public(request, album):
    return _set_visibility(request, album, 'public', 'private')

actions = {
    'publish_all': publish_all,
    'hide_all': hide_all,
    'publish_new': publish_new,
    'publish_hidden': publish_hidden,
    'hide_new': hide_new,
    'hide_public': hide_public,
}

EDITABLE_DATE_FORMAT = '%Y/%m/%d'
def format_editable_date_range(date_range):
    if date_range is None:
        begin = end = datetime.date.today()
    else:
        begin, end = date_range
    return '%s - %s' %(
        begin.strftime(EDITABLE_DATE_FORMAT),
        end.strftime(EDITABLE_DATE_FORMAT)
    )

def default_setter(album, name, value):
    setattr(album, name, value)
    return getattr(album, name)

def cascade_setter(album, name, value):
    prev_value = getattr(album, name, None)
    ret_value = default_setter(album, name, value)
    for photo in album.photos():
        photo_value = getattr(photo, name, None)
        if photo_value is None or photo_value == prev_value:
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
        if name == 'action':
            action = actions.get(value, None)
            if action is not None:
                updated.update(action(request, album))
        elif name in setters:
            updated[name] = setters[name](album, name, value)

    if 'date_range' in updated:
        adjust_photo_dates(album)

    if updated:
        request.app_context.catalog.index(album)

    return JSONResponse(updated)
