import Image
import os

from happy.static import FileResponse

class ImageApplication(object):
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir

    def __call__(self, request):
        fname = request.path_info.rsplit('/', 1)[1]
        cache_file = os.path.join(self.cache_dir, fname)
        if not os.path.exists(cache_file):
            catalog = request.app_context.catalog
            id, dims, ext = fname.split('.')
            req_size = tuple(map(int, dims.split('x')))
            photo = catalog.photo(id).get()
            target_size = _target_size(req_size, photo.size)
            image = photo.image
            image.thumbnail(target_size, Image.ANTIALIAS)
            image.save(cache_file, quality=90)
            os.utime(cache_file, (-1, os.path.getmtime(photo.fpath)))

        return FileResponse(cache_file)

    def version(self, photo, req_size):
        target_size = _target_size(req_size, photo.size)
        return dict(
            fname='%s.%dx%d.jpg' % (photo.id, req_size[0], req_size[1]),
            size=target_size
        )

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
