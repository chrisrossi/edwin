import Image
import os

from happy.acl import has_permission
from happy.static import FileResponse

from webob.exc import HTTPForbidden
from webob.exc import HTTPUnauthorized

class ImageApplication(object):
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir

    def __call__(self, request, fname):
        catalog = request.app_context.catalog
        id, dims, ext = fname.split('.')
        photo = catalog.photo(id).get()
        if not has_permission(request, 'view', photo):
            if request.remote_user:
                return HTTPForbidden()
            return HTTPUnauthorized()

        cache_file = os.path.join(self.cache_dir, fname)
        if not os.path.exists(cache_file):
            req_size = tuple(map(int, dims.split('x')))
            target_size = _target_size(req_size, photo.size)
            image = photo.image
            image.thumbnail(target_size, Image.ANTIALIAS)
            image.save(cache_file, quality=90)
            os.utime(cache_file, (-1, os.path.getmtime(photo.fspath)))

        return FileResponse(cache_file)

    def version(self, photo, req_size):
        target_size = _target_size(req_size, photo.size)
        return dict(
            fname='%s.%dx%d.jpg' % (photo.id, req_size[0], req_size[1]),
            size=target_size
        )

    def clear_cache(self, photo=None):
        cache_dir = self.cache_dir
        for fname in os.listdir(cache_dir):
            if fname.startswith('.'):
                continue
            if photo is None or fname.startswith(photo.id):
                os.remove(os.path.join(cache_dir, fname))

def _target_size(req_size, orig_size):
    # Don't scale up
    if req_size[0] >= orig_size[0] or req_size[1] >= orig_size[1]:
        return orig_size

    # Scale to width, first
    ratio = float(req_size[0]) / orig_size[0]
    new_height = ratio * orig_size[1]
    if new_height <= req_size[1]:
        # Height is in bounds, so return
        return (req_size[0], int(new_height))

    # Otherwise, scale to height instead
    ratio = float(req_size[1]) / orig_size[1]
    new_width = ratio * orig_size[0]
    assert new_width <= req_size[0] # Sanity check
    return (int(new_width), req_size[1])
