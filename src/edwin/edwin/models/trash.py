from __future__ import with_statement

import os
import shutil
import uuid

from happy.traversal import find_model
from happy.traversal import model_path
from edwin.models.photo import Photo

class Trash(object):
    __parent__ = None

    def path(self):
        return os.path.join(self.__parent__.fspath, '.trash')

    def trash(self, context):
        if isinstance(context, Photo):
            return self._trash_photo(context)
        raise ValueError("Cannot trash %s" % type(context))

    def trash_photos_in_album(self, album, photos=None):
        if photos is None:
            photos = album.photos()

        id, folder = self._new_trash(album)

        # Remember how to reinstantiate on restore
        path = model_path(album)
        with open(os.path.join(folder, '.restore'), 'wb') as f:
            f.write('photos|')
            f.write(path)

        for photo in photos:
            # Move photo
            src = photo.fspath
            src_path, src_file = os.path.split(src)
            dst = os.path.join(folder, src_file)
            shutil.move(src, dst)

            # Move metadata
            src = photo._metadata._file
            src_path, src_file = os.path.split(src)
            dst = os.path.join(folder, src_file)
            shutil.move(src, dst)

            # Transformed photo can be recreated, so we delete that
            transformed_path = photo._transformed_path()
            if os.path.exists(transformed_path):
                os.remove(transformed_path)

        return id

    def _new_trash(self, context):
        path = self.path()
        if not os.path.exists(path):
            os.mkdir(path)

        id = str(uuid.uuid1())
        folder = os.path.join(path, id)
        os.mkdir(folder)
        restore_to = context.fspath
        open(os.path.join(folder, '.restore_to'), 'wb').write(restore_to)
        return id, folder

    def _trash_photo(self, photo):
        id, folder = self._new_trash(photo.__parent__)

        # Remember how to reinstantiate on restore
        path = model_path(photo)
        with open(os.path.join(folder, '.restore'), 'wb') as f:
            f.write('photo|')
            f.write(path)

        # Move photo
        src = photo.fspath
        src_path, src_file = os.path.split(src)
        dst = os.path.join(folder, src_file)
        shutil.move(src, dst)

        # Move metadata
        src = photo._metadata._file
        src_path, src_file = os.path.split(src)
        dst = os.path.join(folder, src_file)
        shutil.move(src, dst)

        # Transformed photo can be recreated, so we delete that
        transformed_path = photo._transformed_path()
        if os.path.exists(transformed_path):
            os.remove(transformed_path)

        return id

    def restore(self, id, catalog=None):
        src_path = os.path.join(self.path(), id)
        dst_path = open(os.path.join(src_path, '.restore_to'), 'rb').read()
        for fname in os.listdir(src_path):
            if fname in ('.', '..', '.restore_to', '.restore'):
                continue

            src = os.path.join(src_path, fname)
            dst = os.path.join(dst_path, fname)
            shutil.move(src, dst)

        root = self.__parent__
        restore  = open(os.path.join(src_path, '.restore'), 'rb').read()
        if restore.startswith('photo|'):
            path = restore[6:]
            restored = find_model(root, path)
            if catalog is not None:
                catalog.index(restored)

        elif restore.startswith('photos|'):
            path = restore[7:]
            restored = find_model(root, path)
            if catalog is not None:
                catalog.index_album_and_photos(restored)

        shutil.rmtree(src_path)

        return restored
