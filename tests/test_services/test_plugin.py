#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.services.plugins import ArgumentsPlugin


class TestPlugin(unittest.TestCase):

    def setUp(self):
        self.arguments = ArgumentsPlugin()

        def fn(args):
            self.args = args
        self.cb = self.arguments.apply(fn, mock.Mock())

    def test_call_kw(self):
        self.cb(f0='a', f1='b', f2='c')
        self.assertEqual(tuple(self.args), ('a', 'b', 'c'))

    def test_call_kw_gap(self):
        self.cb(f0='a', f1='b', f3='c')
        self.assertEqual(tuple(self.args), ('a', 'b'))
