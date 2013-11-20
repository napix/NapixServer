#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest2
import napixd
from cStringIO import StringIO
import mock

from napixd.conf import Conf, DEFAULT_CONF


class TestConf(unittest2.TestCase):

    def setUp(self):
        self.conf = Conf({
            'a': {
                'a1': {
                    'a1a': 'foo',
                    'a1b': 'bar'
                },
                'a2': {
                    'x': 1,
                    'y': 2
                }
            },
            'b': {
                'mpm': 'prefork'
            },
            'c': 'blo'
        })

    def test_get(self):
        self.assertEqual(self.conf.get('c'), 'blo')

    def test_get_inexisting(self):
        self.assertEqual(self.conf.get('d'), {})

    def test_get_default(self):
        self.assertEqual(self.conf.get('d', None), None)
        self.assertEqual(self.conf.get('d', 123), 123)

    def test_get_dotted(self):
        self.assertEqual(self.conf.get('a.a1.a1b'), 'bar')
        self.assertEqual(self.conf.get('b.mpm'), 'prefork')

    def test_contains_in(self):
        self.assertTrue('a' in self.conf)
        self.assertTrue('a.a1.a1a' in self.conf)

    def test_contains_not_in(self):
        self.assertFalse('e' in self.conf)
        self.assertFalse('a.a2.z' in self.conf)

    def test_inherit(self):
        self.assertEqual(self.conf.get('a').get('a1').get('a1a'), 'foo')
        self.assertEqual(self.conf.get('a').get('a2'), {'x': 1, 'y': 2})

    def test_not_truthy(self):
        self.assertFalse(bool(self.conf.get('d')))

    def test_truthy(self):
        self.assertTrue(bool(self.conf.get('a')))
        self.assertTrue(bool(self.conf.get('c')))


class TestConfComment(unittest2.TestCase):

    def setUp(self):
        self.conf = Conf({
            'a': 'abc',
            '#a': 'this is three letters'
        })

    def test_comment_items(self):
        self.assertEqual(self.conf.items(), [('a', 'abc')])

    def test_comment_keys(self):
        self.assertEqual(self.conf.keys(), ['a'])


class TestConfLoader(unittest2.TestCase):
    good_json1 = '{"json" : { "v" : 1 } }'
    good_json2 = '{"json" : { "v" : 2 } }'
    bad_json = '{"badjson'
    conf_file = napixd.get_file('conf/settings.json', create=False)

    def setUp(self):
        self.patch_open = mock.patch(
            'napixd.conf.open', side_effect=self._open, spec=open)

    def _open(self, filename, mode='r'):
        if filename == DEFAULT_CONF and mode.startswith('r'):
            return open(DEFAULT_CONF)
        elif mode.startswith('w'):
            return mock.MagicMock()
        elif not filename in self.filesystem:
            raise IOError('No such file or directory')
        else:
            return StringIO(self.filesystem[filename])

    def test_bad_json(self):
        self.filesystem = {
            '/etc/napixd/settings.json': self.bad_json,
            self.conf_file: self.good_json2
        }
        with self.patch_open:
            conf = Conf.make_default()
        self.assertTrue('v' in conf['json'])
        self.assertEqual(conf.get('json.v'), 2)

    def test_load_system(self):
        self.filesystem = {
            '/etc/napixd/settings.json': self.good_json1,
        }

        with self.patch_open as patched_open:
            conf = Conf.make_default()
        self.assertTrue('v' in conf['json'])
        self.assertEqual(len(patched_open.mock_calls), 2)

    def test_load_multiple(self):
        self.filesystem = {
            '/etc/napixd/settings.json': self.good_json2,
            self.conf_file: self.good_json1
        }
        with self.patch_open:
            conf = Conf.make_default()
        self.assertTrue('v' in conf['json'])
        self.assertEqual(conf.get('json.v'), 1)

    def test_load_sources(self):
        self.filesystem = {
            self.conf_file: self.good_json2
        }
        with self.patch_open:
            conf = Conf.make_default()
        self.assertTrue('v' in conf['json'])

    def test_get_default(self):
        self.filesystem = {
            '/etc/napixd/settings.json': self.good_json2,
            self.conf_file: self.good_json1
        }
        with self.patch_open:
            Conf.make_default()
        self.assertEqual(Conf.get_default(), {'json': {'v': 1}})
        self.assertEqual(Conf.get_default('json'), {'v': 1})
        self.assertEqual(Conf.get_default('json.v'), 1)

    def test_write_default(self):
        self.filesystem = {}
        with self.patch_open as open:
            Conf.make_default()
        self.assertTrue(mock.call(self.conf_file, 'w') in open.call_args_list)

    def test_no_file(self):
        self.filesystem = {}
        with self.patch_open:
            conf = Conf.make_default()
        self.assertEqual(conf.keys(), ['Napix'])
        self.assertTrue('Napix.managers' in conf)


class TestDotted(unittest2.TestCase):

    def setUp(self):
        self.conf = Conf({
            'a': {
                'b': 1,
                'c.d.e': 2
            },
            'b': {
                'c': {
                    'd': 4,
                },
                'c.d': 5
            }
        })

    def test_get_dotted_prefix(self):
        a = self.conf.get('a')
        self.assertEqual(a.get('c.d.e'), 2)

    def test_get_dotted(self):
        self.assertEqual(self.conf.get('a.c.d.e'), 2)

    def test_contains(self):
        self.assertTrue('a.c.d.e' in self.conf)

    def test_contains_not_in_prefix(self):
        self.assertFalse('a.c.d' in self.conf)

    def test_get_conflict(self):
        self.assertEqual(self.conf.get('b.c.d'), 5)
        self.assertEqual(self.conf.get('b.c'), {'d': 4})


class TestConfType(unittest2.TestCase):
    def setUp(self):
        self.conf = Conf({
            'int': 1,
            'str': 'abc',
            'dict': {
                'a': 1
            },
            'list': [1, 2, 3]
        })

    def test_get_type(self):
        self.assertEqual(self.conf.get('int', type=int), 1)

    def test_get_bad_type(self):
        self.assertRaises(TypeError, self.conf.get, 'int', type=str)

    def test_get_type_dict(self):
        v = self.conf.get('dict', type=dict)
        self.assertEqual(v, {'a': 1})
        self.assertTrue(isinstance(v, Conf))
