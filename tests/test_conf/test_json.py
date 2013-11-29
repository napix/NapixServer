#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest

from napixd.conf.json import Conf, CompatConf


class TestConf(unittest.TestCase):

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


class TestConfComment(unittest.TestCase):

    def setUp(self):
        self.conf = Conf({
            'a': 'abc',
            '#a': 'this is three letters'
        })

    def test_length(self):
        self.assertEqual(len(self.conf), 1)

    def test_comment_items(self):
        self.assertEqual(self.conf.items(), [('a', 'abc')])

    def test_comment_keys(self):
        self.assertEqual(self.conf.keys(), ['a'])

    def test_truth_value(self):
        conf = Conf({
            '#a': 1
        })
        self.assertFalse(bool(conf))


class TestDotted(unittest.TestCase):

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


class TestConfType(unittest.TestCase):
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


class TestCompatConf(unittest.TestCase):
    def setUp(self):
        self.conf = CompatConf(Conf({
            'Napix': {
                'service': 'napix.io',
            },
            'local': {
                'hostname': 'napix.io'
            }
        }))

    def test_compat_napix(self):
        self.assertEqual(self.conf.get('service'), 'napix.io')

    def test_compat_manager(self):
        self.assertEqual(self.conf.get('Manager local.hostname'), 'napix.io')
