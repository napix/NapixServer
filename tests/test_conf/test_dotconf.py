#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest

try:
    from napixd.conf.dotconf import ConfFactory
except ImportError:
    __test__ = False


class TestDotconf(unittest.TestCase):
    def setUp(self):
        self.conf = ConfFactory().parse_string('''
a = 1
b {
    c = 'd'
    ss 'd' {
        ghi = 4
    }
}
e {
    g = 0
    h {
    }
}
e 'f' {
    g = 1
}
e 'h' {
    g = 2
}
s 'a.b.c' {
    def = 3
}
''')

    def test_contains_variable(self):
        self.assertTrue('a' in self.conf)

    def test_contains_block(self):
        self.assertTrue('e' in self.conf)

    def test_contains_named_block(self):
        self.assertTrue('e h' in self.conf)

    def test_contains_named_and_dots(self):
        self.assertTrue('s a.b.c' in self.conf)

    def test_contains_named_empty(self):
        self.assertTrue('b.c' in self.conf)

    def test_contains_span(self):
        self.assertTrue('h' in self.conf['e'])

    def test_contains_variable_not(self):
        self.assertFalse('z' in self.conf)

    def test_bool_value(self):
        self.assertTrue(bool(self.conf['e']))
        self.assertFalse(bool(self.conf['e.h']))

    def test_get_value(self):
        self.assertEqual(self.conf['a'], 1)

    def test_get_section_named_inside_section(self):
        self.assertEqual(self.conf['b.ss d.ghi'], 4)

    def test_get_value_not_exists(self):
        self.assertRaises(KeyError, self.conf.__getitem__, 'd')

    def test_get_accross_section(self):
        self.assertEqual(self.conf['b.c'], 'd')

    def test_get_accross_section_not_exists_key(self):
        self.assertRaises(KeyError, self.conf.__getitem__, 'b.d')

    def test_get_accross_section_not_exists_section(self):
        self.assertRaises(KeyError, self.conf.__getitem__, 'g.d')

    def test_get_accross_section_not_section(self):
        self.assertRaises(KeyError, self.conf.__getitem__, 'a.c')

    def test_list(self):
        self.assertEqual(sorted(list(self.conf)),
                         ['a', 'b', 'e', 'e f', 'e h', 's a.b.c'])

    def test_get_section_with_dots(self):
        self.assertEqual(self.conf['s a.b.c.def'], 3)
        section = self.conf['s a.b.c']
        self.assertEqual(section['def'], 3)

    def test_get_accross_section_named(self):
        self.assertEqual(self.conf['e.g'], 0)
        self.assertEqual(self.conf['e f.g'], 1)
        self.assertEqual(self.conf['e h.g'], 2)

    def test_get_section_named_not_exists(self):
        self.assertRaises(KeyError, self.conf.__getitem__, 'b.ss')
        self.assertRaises(KeyError, self.conf.__getitem__, 's')

    def test_get_accross_section_named_not_exists(self):
        self.assertRaises(KeyError, self.conf.__getitem__, 'e i.g')

    def test_get_section(self):
        section = self.conf['b']
        self.assertEqual(section['c'], 'd')
        self.assertEqual(list(section), ['c', 'ss d'])
