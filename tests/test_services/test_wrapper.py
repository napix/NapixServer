#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.services.wrapper import ResourceWrapper


class TestWrapper(unittest.TestCase):
    def test_evaluation(self):
        mgr = mock.Mock()
        rw = ResourceWrapper(mgr, 'id')
        self.assertEqual(rw.resource, mgr.get_resource.return_value)

    def test_evaluated(self):
        mgr = mock.Mock()
        resource = mock.Mock()
        rw = ResourceWrapper(mgr, 'id', resource)
        self.assertEqual(rw.resource, resource)
        self.assertEqual(mgr.get_resource.call_count, 0)

    def test_dict(self):
        mgr = mock.Mock()
        rw = ResourceWrapper(mgr, 'id', {'a': 1})
        self.assertEqual(dict(rw), {'a': 1})

    def test_loaded_init(self):
        mgr = mock.Mock()
        rw = ResourceWrapper(mgr, 'id', {'a': 1})
        self.assertTrue(rw.loaded)

    def test_loaded(self):
        mgr = mock.Mock()
        rw = ResourceWrapper(mgr, 'id')
        self.assertFalse(rw.loaded)
        rw.resource
        self.assertTrue(rw.loaded)
