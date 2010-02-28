from __future__ import with_statement

import os
import shutil
import uuid

from edwin.models.photo import Photo

class Trash(object):
    __parent__ = None

    def path(self):
        return os.path.join(self.__parent__.path, '.trash')

    def trash(self, context):
        if isinstance(context, Photo):
            return self._trash_photo(context)
        raise ValueError("Cannot trash %s" % type(context))

    def _new_trash(self, context):
        path = self.path()
        if not os.path.exists(path):
            os.mkdir(path)

        id = str(uuid.uuid1())
        folder = os.path.join(path, id)
        os.mkdir(folder)
        restore_to = context.__parent__.path
        open(os.path.join(folder, '.restore_to'), 'wb').write(restore_to)
        return id, folder

    def _trash_photo(self, photo):
        id, folder = self._new_trash(photo)

        # Remember how to reinstantiate on restore
        with open(os.path.join(folder, '.restore'), 'wb') as f:
            f.write('photo|')
            f.write(photo.fpath)

        # Move photo
        src = photo.fpath
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

    def restore(self, id):
        src_path = os.path.join(self.path(), id)
        dst_path = open(os.path.join(src_path, '.restore_to'), 'rb').read()
        for fname in os.listdir(src_path):
            if fname in ('.', '..', '.restore_to', '.restore'):
                continue

            src = os.path.join(src_path, fname)
            dst = os.path.join(dst_path, fname)
            shutil.move(src, dst)

        restore  = open(os.path.join(src_path, '.restore'), 'rb').read()
        if restore.startswith('photo|'):
            fpath = restore.split('|')[1]
            restored = Photo(fpath)

        shutil.rmtree(src_path)

        return restored
