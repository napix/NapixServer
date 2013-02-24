#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import unittest2

from tests.mock.managers import manager, managed, manager_direct
from napixd.services import Service, CollectionService

class TestServiceEmpty( unittest2.TestCase):
    def setUp(self):
        self.service = Service( managed)

    def test_collection_service(self):
        self.assertTrue(all( isinstance( s, CollectionService )
            for s in self.service.collection_services ))
        self.assertEqual( len( self.service.collection_services), 1)

    def test_set_bottle(self):
        bottle = mock.Mock()
        self.service.setup_bottle( bottle)
        self.assertSetEqual(set( mc[1][0] for mc in bottle.mock_calls ),
                set([
                    '/my-mock',
                    '/my-mock/',
                    '/my-mock/:f0',
                    '/my-mock/_napix_help',
                    '/my-mock/_napix_new',
                    '/my-mock/_napix_resource_fields',
                    ]))

class TestServiceWithManaged( unittest2.TestCase):
    def setUp(self):
        self.service = Service( manager)

    def test_collection_service(self):
        self.assertTrue(all( isinstance( s, CollectionService )
            for s in self.service.collection_services ))
        self.assertEqual( len( self.service.collection_services), 2)

    def test_set_bottle(self):
        bottle = mock.Mock()
        self.service.setup_bottle( bottle)
        self.assertSetEqual(set( mc[1][0] for mc in bottle.mock_calls ),
                set([
                    '/this-mock',
                    '/this-mock/',
                    '/this-mock/:f0',
                    '/this-mock/_napix_help',
                    '/this-mock/_napix_new',
                    '/this-mock/_napix_resource_fields',
                    '/this-mock/:f0/',
                    '/this-mock/:f0/my-mock/',
                    '/this-mock/:f0/my-mock/:f1',
                    '/this-mock/:f0/my-mock/_napix_help',
                    '/this-mock/:f0/my-mock/_napix_new',
                    '/this-mock/:f0/my-mock/_napix_resource_fields',
                    ]))

class TestServiceWithManagedDirect( unittest2.TestCase):
    def setUp(self):
        self.service = Service( manager_direct)

    def test_collection_service(self):
        self.assertTrue(all( isinstance( s, CollectionService )
            for s in self.service.collection_services ))
        self.assertEqual( len( self.service.collection_services), 2)

    def test_set_bottle(self):
        bottle = mock.Mock()
        self.service.setup_bottle( bottle)
        self.assertSetEqual(set( mc[1][0] for mc in bottle.mock_calls ),
                set([
                    '/this-mock',
                    '/this-mock/',
                    '/this-mock/:f0',
                    '/this-mock/_napix_help',
                    '/this-mock/_napix_new',
                    '/this-mock/_napix_resource_fields',
                    '/this-mock/:f0/',
                    '/this-mock/:f0/',
                    '/this-mock/:f0/:f1',
                    '/this-mock/:f0/_napix_help',
                    '/this-mock/:f0/_napix_new',
                    '/this-mock/:f0/_napix_resource_fields',
                    ]))

