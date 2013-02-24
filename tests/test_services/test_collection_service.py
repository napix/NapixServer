#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest2

from napixd.conf import Conf
from napixd.services import CollectionService, FirstCollectionService

from tests.mock.managers import manager, managed


class TestCollectionServiceManaged(unittest2.TestCase):
    def setUp(self):
        self.fcs = FirstCollectionService( manager, Conf(), 'parent')
        self.cs = CollectionService( self.fcs, managed, Conf(), 'child')

    def test_service_stack(self):
        self.assertListEqual( self.cs.services, [ self.fcs, self.cs ])


    def test_managed_classes(self):
        managed_classes_url = self.fcs.as_managed_classes([ 'p1'])
        self.assertListEqual( managed_classes_url, [ '/parent/p1/my-mock' ])
        #Should be this one
        #self.assertListEqual( managed_classes_url, [ '/parent/p1/child/' ])

    def test_get_managers(self):
        all, this = self.cs.get_managers([ 'p1' ])
        self.assertEqual( managed(), this)

        manager_, id, resource = all[0]
        self.assertEqual( manager(), manager_)
        manager().validate_id.assert_called_once_with( 'p1')
        self.assertEqual( id, manager().validate_id())
        manager().get_resource.assert_called_once_with( id)
        self.assertEqual( resource, manager().get_resource())


