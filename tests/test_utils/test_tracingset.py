#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from napixd.utils.tracingset import TracingSet


class TestTracingSet(unittest.TestCase):
    def setUp(self):
        self.set = TracingSet([
            'abc',
            'nodef',
        ])

    def test_check_empty(self):
        self.assertEqual(self.set.checked, set())
        self.assertEqual(self.set.unchecked, set([
            'abc',
            'nodef',
        ]))

    def test_contains(self):
        self.assertTrue('abc' in self.set)
        self.assertTrue('klm' not in self.set)

    def test_check(self):
        self.assertTrue('abc' in self.set)
        self.assertEqual(self.set.checked, set([
            'abc',
        ]))
        self.assertEqual(self.set.unchecked, set([
            'nodef',
        ]))

    def test_no_check(self):
        self.assertFalse('def' in self.set)
        self.assertEqual(self.set.checked, set([
            'def'
        ]))
        self.assertEqual(self.set.unchecked, set([
            'abc'
        ]))
