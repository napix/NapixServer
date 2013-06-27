#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.managers.base import Manager
from napixd.managers.managed_classes import ManagedClass


class TestManagedClass( unittest.TestCase):
    def setUp(self):
        self.manager = mock.MagicMock( spec=Manager, __name__='my-mock')

    def test_is_resolved(self):
        mc = ManagedClass( 'a.b.C')
        self.assertFalse( mc.is_resolved())

    def test_resovle(self):
        mc = ManagedClass( 'a.b.C')
        mc.resolve( self.manager)
        self.assertTrue( mc.is_resolved())

    def test_name_not_resolved(self):
        mc = ManagedClass( 'a.b.C')
        self.assertRaises( ValueError, mc.get_name)

    def test_name(self):
        mc = ManagedClass( self.manager)
        self.assertEqual( mc.get_name(), self.manager.get_name())

    def test_rewrite_name(self):
        mc = ManagedClass( self.manager, name='other')
        self.assertEqual( mc.get_name(), 'other')

    def test_rewrite_extractor(self):
        extractor = mock.Mock()
        mc = ManagedClass( self.manager, extractor=extractor)
        self.assertEqual( mc.extractor, extractor)

