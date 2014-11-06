#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest

import decimal

from napixd.utils.json import JSONProvider


class TestJSONEncoder(unittest.TestCase):
    def prov(self, pprint=False, decimal=False):
        return JSONProvider(pprint, decimal)

    def test_encode_decimal(self):
        p = self.prov(decimal=True)
        self.assertEqual(p.dumps(decimal.Decimal('1.13')), '1.13')

    def test_encode_decimal_dict(self):
        p = self.prov(decimal=True)
        self.assertEqual(p.dumps({'a': decimal.Decimal('1.13')}), '{"a": 1.13}')

    def test_decode_decimal(self):
        p = self.prov(decimal=True)
        value = p.loads('{"a": 1.13, "b": 1}')
        self.assertEqual(value, {'a': decimal.Decimal('1.13'), 'b': 1})
        self.assertTrue(isinstance(value['a'], decimal.Decimal))
        self.assertTrue(isinstance(value['b'], int))

    def test_encode_indent(self):
        p = self.prov(pprint=True)
        self.assertEqual(p.dumps({'a': 1, 'b': 2}),
                         '''{\n    "a": 1, \n    "b": 2\n}''')
