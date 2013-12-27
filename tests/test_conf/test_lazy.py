#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
import mock

from napixd.conf.lazy import LazyConf


class TestLazyConf(unittest.TestCase):
    def setUp(self):
        self.key = 'key'
        self.source = mock.MagicMock()
        self.conf = self.source.get_default.return_value

    def lazy(self):
        return LazyConf(self.key, source=self.source)

    def test_not_evaluated(self):
        self.lazy()
        self.assertEqual(self.source.get_default.call_count, 0)

    def test_get(self):
        self.assertEqual(self.lazy().get, self.conf.get)

    def test_getitem(self):
        c = self.lazy()
        self.assertEqual(c['a'], self.conf.__getitem__.return_value)

    def test_not_revaludated(self):
        c = self.lazy()
        c.get('a')
        c['b']
        self.assertEqual(self.source.get_default.call_count, 1)
