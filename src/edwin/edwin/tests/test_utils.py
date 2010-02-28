import unittest

class Test_find_trash(unittest.TestCase):
    def fut(self):
        from edwin.utils import find_trash
        return find_trash

    def test_find_existing_trash(self):
        root = DummyModel()
        context = root['foo'] = DummyModel()
        trash = root.trash = DummyTrash()

        self.assertEqual(self.fut()(root), trash)
        self.assertEqual(self.fut()(context), trash)

    def test_create_new_trash(self):
        root = DummyModel()
        context = root['foo'] = DummyModel()
        trash = DummyTrash()
        def factory():
            return trash

        self.assertEqual(self.fut()(root, Trash=factory), trash)
        self.assertEqual(root.trash, trash)

        del root.trash
        self.assertEqual(self.fut()(context, Trash=factory), trash)
        self.assertEqual(root.trash, trash)

class DummyModel(dict):
    __parent__ = None
    __name__ = None

    def __setitem__(self, name, child):
        super(DummyModel, self).__setitem__(name, child)
        child.__name__ = name
        child.__parent__ = self

class DummyTrash(object):
    pass
