from edwin.models.trash import Trash

def find_root(context):
    parent = getattr(context, '__parent__', None)
    while parent is not None:
        context = parent
        parent = getattr(context, '__parent__', None)
    return context

def find_trash(context, Trash=Trash):
    root = find_root(context)
    trash = getattr(root, 'trash', None)
    if trash is None:
        trash = root.trash = Trash()
    return trash
