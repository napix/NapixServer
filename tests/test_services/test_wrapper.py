#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.services.wrapper import ResourceWrapper


class TestWrapper(unittest.TestCase):
    def setUp(self):
        self.mgr = mock.Mock()
        self.resource = None

    def rw(self):
        return ResourceWrapper(self.mgr, 'id', self.resource)

    def test_evaluation(self):
        rw = self.rw()
        self.assertEqual(rw.resource, self.mgr.get_resource.return_value)

    def test_evaluated(self):
        self.resource = mock.Mock()
        rw = self.rw()
        self.assertEqual(rw.resource, self.resource)
        self.assertEqual(self.mgr.get_resource.call_count, 0)

    def test_dict(self):
        self.resource = {'a': 1}
        self.assertEqual(dict(self.rw()), {'a': 1})

    def test_loaded_init(self):
        self.resource = {'a': 1}
        self.assertTrue(self.rw().loaded)

    def test_loaded(self):
        rw = self.rw()
        self.assertFalse(rw.loaded)
        rw.resource
        self.assertTrue(rw.loaded)


class TestWrapperObject(unittest.TestCase):
    def setUp(self):
        self.mgr = mock.Mock()
        self.resource = mock.Mock()
        self.rw = ResourceWrapper(self.mgr, 'id', self.resource)

    def test_object_getitem(self):
        self.assertRaises(ValueError, lambda: self.rw[1])

    def test_object_iter(self):
        self.assertRaises(ValueError, iter, self.rw)

    def test_object_len(self):
        self.assertRaises(ValueError, len, self.rw)
