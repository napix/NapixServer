#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
import mock

from napixd.conf import ConfLoader, EmptyConf, BaseConf


class ConfFactory(object):
    def get_filename(self):
        pass

    def parse_string(self, string):
        pass

    def parse_file(self, handle):
        pass


class TestConfLoader(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.patch_isfile = mock.patch('os.path.isfile')
        cls.patch_open = mock.patch('__builtin__.open')

    def setUp(self):
        self.factory = f = mock.Mock(spec=ConfFactory)
        f.get_filename.return_value = 'settings.test'

        self.paths = ['/a/', '/b/']
        self.isfile = self.patch_isfile.start()
        self.Open = self.patch_open.start()
        self.open = o = self.Open.return_value
        o.__enter__.return_value = o

    def tearDown(self):
        self.patch_isfile.stop()
        self.patch_open.stop()

    def get_loader(self):
        return ConfLoader(self.paths, self.factory)

    def call(self):
        loader = self.get_loader()
        return loader()

    def test_loader(self):
        self.isfile.side_effect = lambda x: x == '/a/settings.test'

        self.assertEqual(self.call(), self.factory.parse_file.return_value)
        self.factory.parse_file.assert_called_once_with(self.open)
        self.Open.assert_called_once_with('/a/settings.test', 'rb')

    def test_file_loader(self):
        self.isfile.side_effect = lambda x: x == '/a/settings.test'
        self.factory.parse_file.side_effect = IOError()

        self.assertRaises(IOError, self.call)

    def test_copy_error(self):
        self.isfile.return_value = False

        self.Open.side_effect = IOError()
        conf = self.call()

        self.assertEqual(conf, EmptyConf())

    def test_copy(self):
        self.isfile.return_value = False

        with mock.patch('napixd.conf.__file__', '/source/__init__.py'):
            conf = self.call()

        self.Open.assert_has_calls([
            mock.call('/source/settings.test', 'rb'),
            mock.call('/a/settings.test', 'wb'),
        ], any_order=True)

        self.assertEqual(conf, self.factory.parse_file.return_value)


class MyConf(BaseConf):
    def __init__(self, value):
        self.value = value

    def __getitem__(self, key):
        if key == 'key':
            return self.value
        raise KeyError()

    def __iter__(self):
        return iter(['key'])

    def __len__(self):
        return 1


class TestBaseConf(unittest.TestCase):
    def setUp(self):
        self.c = MyConf(1)

    def test_get(self):
        self.assertEqual(self.c.get('key'), 1)

    def test_get_not(self):
        self.assertEqual(self.c.get('this'), EmptyConf())

    def test_get_type(self):
        self.assertEqual(self.c.get('key', type=int), 1)

    def test_get_type_tuple(self):
        self.assertEqual(self.c.get('key', type=(int, unicode)), 1)

    def test_get_type_tuple_bad(self):
        self.assertRaises(TypeError, self.c.get, 'key', type=(unicode, list))

    def test_get_type_bad(self):
        self.assertRaises(TypeError, self.c.get, 'key', type=unicode)

    def test_get_type_no_key(self):
        self.assertRaises(TypeError, self.c.get, 'this', type=unicode)

    def test_get_default_exists(self):
        self.assertEqual(self.c.get('key', 2), 1)

    def test_get_default_not(self):
        self.assertEqual(self.c.get('that', 2), 2)

    def test_get_default_none(self):
        self.assertEqual(self.c.get('that', None), None)

    def test_get_default_type(self):
        self.assertEqual(self.c.get('that', 12, type=int), 12)

    def test_get_default_bad_type(self):
        self.assertRaises(TypeError, self.c.get, 'key', '12', type=unicode)
