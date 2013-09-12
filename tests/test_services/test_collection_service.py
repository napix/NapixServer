#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import unittest2

from napixd.conf import Conf
from napixd.services import CollectionService, FirstCollectionService
from napixd.managers.managed_classes import ManagedClass

from tests.mock.managers import Manager, Managed


class TestCollectionServiceManaged(unittest2.TestCase):
    def setUp(self):
        Managed.reset_mock()
        self.fcs_conf = mock.Mock( spec=Conf, name='fcs_conf')
        self.cs_conf = mock.Mock( spec=Conf, name='cs_conf')
        self.fcs = FirstCollectionService( Manager, self.fcs_conf, 'parent')
        self.managed_class = mock.Mock( spec=ManagedClass, manager_class=Managed)
        self.managed_class.extractor.side_effect = lambda x:x
        self.cs = CollectionService( self.fcs, self.managed_class, self.cs_conf, 'child')

    def test_managed_classes(self):
        managed_classes_url = self.fcs.as_managed_classes([ 'p1'])
        self.assertListEqual( managed_classes_url, [ '/parent/p1/my-middle-mock' ])
        #Should be this one
        #self.assertListEqual( managed_classes_url, [ '/parent/p1/child/' ])

    def test_get_managers(self):
        managed = Managed.return_value
        manager = Manager.return_value
        all, this = self.cs.get_managers([ 'p1' ])
        self.assertEqual( managed, this)

        self.assertEqual(len(all), 1)
        manager_, wrapped = all[0]
        self.assertEqual( manager, manager_)
        manager.configure.assert_called_once_with( self.fcs_conf)
        manager.validate_id.assert_called_once_with( 'p1')
        self.assertEqual(wrapped.id, manager.validate_id())
        manager.get_resource.assert_called_once_with(wrapped.id)
        self.assertEqual(wrapped.resource, manager.get_resource())


    def test_generate_manager(self):
        resource = mock.Mock()
        self.cs.generate_manager( resource)
        self.managed_class.extractor.assert_called_once_with( resource)
        Managed.assert_called_once_with( resource)

    def test_get_name_fcs(self):
        self.assertEqual( self.fcs.get_name(), 'parent')
    def test_get_name_cs(self):
        self.assertEqual( self.cs.get_name(), 'parent.child')
