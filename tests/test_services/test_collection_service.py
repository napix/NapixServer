#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import unittest2

from napixd.conf import Conf
from napixd.services import CollectionService, FirstCollectionService
from napixd.managers.managed_classes import ManagedClass

from tests.mock.managers import manager, managed


class TestCollectionServiceManaged(unittest2.TestCase):
    def setUp(self):
        managed.reset_mock()
        self.fcs_conf = mock.Mock( spec=Conf, name='fcs_conf')
        self.cs_conf = mock.Mock( spec=Conf, name='cs_conf')
        self.fcs = FirstCollectionService( manager, self.fcs_conf, 'parent')
        self.managed_class = mock.Mock( spec=ManagedClass, manager_class=managed)
        self.managed_class.extractor.side_effect = lambda x:x
        self.cs = CollectionService( self.fcs, self.managed_class, self.cs_conf, 'child')

    def test_service_stack(self):
        self.assertListEqual( self.cs.services, [ self.fcs, self.cs ])

    def test_managed_classes(self):
        managed_classes_url = self.fcs.as_managed_classes([ 'p1'])
        self.assertListEqual( managed_classes_url, [ '/parent/p1/my-middle-mock' ])
        #Should be this one
        #self.assertListEqual( managed_classes_url, [ '/parent/p1/child/' ])

    def test_get_managers(self):
        all, this = self.cs.get_managers([ 'p1' ])
        self.assertEqual( managed(), this)

        manager_, id, resource = all[0]
        self.assertEqual( manager(), manager_)
        manager().configure.assert_called_once_with( self.fcs_conf)
        manager().validate_id.assert_called_once_with( 'p1')
        self.assertEqual( id, manager().validate_id())
        manager().get_resource.assert_called_once_with( id)
        self.assertEqual( resource, manager().get_resource())


    def test_generate_manager(self):
        resource = mock.Mock()
        self.cs.generate_manager( resource)
        self.managed_class.extractor.assert_called_once_with( resource)
        managed.assert_called_once_with( resource)
