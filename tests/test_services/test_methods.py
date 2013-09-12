#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import unittest
import mock
from napixd.services.methods import Implementation


class TestImplementation(unittest.TestCase):

    def setUp(self):
        self.mgr = type('M', (object,), {})

    def test_nofilter(self):
        self.mgr.get_resource = mock.Mock()
        self.mgr.list_resource = mock.Mock()
        impl = Implementation(self.mgr)
        self.assertTrue('get_all_resources' in impl)
        self.assertFalse('get_all_resources_filter' in impl)

    def test_filter(self):
        gr = self.mgr.get_resource = mock.Mock()
        self.mgr.list_resource = mock.Mock()
        self.mgr.list_resource_filter = mock.Mock()
        impl = Implementation(self.mgr)
        self.assertTrue('get_all_resources' in impl)
        self.assertTrue('get_all_resources_filter' in impl)
        self.assertEqual(impl.get_resource, gr)
