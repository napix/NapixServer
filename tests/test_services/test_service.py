#!/usr/bin/env pysource)
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import unittest2

from tests.mock.managers import Manager, Managed, Manager_direct
from napixd.services import Service
from napixd.services.collectionservice import BaseCollectionService
from napixd.conf import Conf
from napixd.managers import ManagedClass

class TestServiceEmpty( unittest2.TestCase):
    def setUp(self):
        self.service = Service( Managed)

    def test_collection_service(self):
        self.assertTrue(all( isinstance( s, BaseCollectionService )
            for s in self.service.collection_services ))
        self.assertEqual( len( self.service.collection_services), 1)

    def test_set_bottle(self):
        bottle = mock.Mock()
        self.service.setup_bottle( bottle)
        self.assertSetEqual(set( mc[0][0] for mc in bottle.route.call_args_list ),
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
        self.service = Service( Manager)

    def test_collection_service(self):
        self.assertTrue(all( isinstance( s, BaseCollectionService)
            for s in self.service.collection_services ))
        self.assertEqual( len( self.service.collection_services), 2)

    def test_set_bottle(self):
        bottle = mock.Mock()
        self.service.setup_bottle( bottle)
        self.assertSetEqual(set( mc[0][0] for mc in bottle.route.call_args_list ),
                set([
                    '/this-mock',
                    '/this-mock/',
                    '/this-mock/:f0',
                    '/this-mock/_napix_help',
                    '/this-mock/_napix_new',
                    '/this-mock/_napix_resource_fields',
                    '/this-mock/:f0/',
                    '/this-mock/:f0/my-middle-mock',
                    '/this-mock/:f0/my-middle-mock/',
                    '/this-mock/:f0/my-middle-mock/:f1',
                    '/this-mock/:f0/my-middle-mock/_napix_help',
                    '/this-mock/:f0/my-middle-mock/_napix_new',
                    '/this-mock/:f0/my-middle-mock/_napix_resource_fields',
                    ]))

class TestServiceWithManagedDirect( unittest2.TestCase):
    def setUp(self):
        self.service = Service( Manager_direct)

    def test_collection_service(self):
        self.assertTrue(all( isinstance( s, BaseCollectionService )
            for s in self.service.collection_services ))
        self.assertEqual( len( self.service.collection_services), 2)

    def test_set_bottle(self):
        bottle = mock.Mock()
        self.service.setup_bottle( bottle)
        self.assertSetEqual(set( mc[0][0] for mc in bottle.route.call_args_list ),
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

def FakeCS( *args ):
    if len( args) == 4:
        ps, mc, cf, ns = args
    else:
        ps = None
        mc, cf, ns = args
    name = '{0}.{1}'.format( ps.get_name(), ns) if ps else ns
    mk = mock.Mock( spec=BaseCollectionService, name='Service:'+name)
    mk.get_name.return_value = name
    return mk


class TestServiceServiceCollection(unittest2.TestCase):
    def setUp(self):
        self.config = mock.Mock( spec=Conf)
        self.config.get.side_effect = lambda x:x
        self.CS = CS = mock.Mock( spec=BaseCollectionService, side_effect=FakeCS)

        self.manager = mock.Mock( name='root')
        self.patch_cs = mock.patch.multiple( 'napixd.services', FirstCollectionService=CS, CollectionService=CS)

        self.m1 = mock.Mock( name='m1' )
        self.m1.direct_plug.return_value = None
        self.mc1 = mock.Mock( spec=ManagedClass, manager_class=self.m1, name='mc1' )
        self.mc1.get_name.return_value = 'mc1'

        self.m2 = mock.Mock( name='m2' )
        self.m2.direct_plug.return_value = True
        self.m2.get_managed_classes.return_value = [ self.mc1 ]
        self.mc2 = mock.Mock( spec=ManagedClass, manager_class=self.m2, name='mc2' )
        self.mc2.get_name.return_value = 'mc2'

    def test_config_managed_class(self):
        self.manager.direct_plug.return_value = False
        self.manager.get_managed_classes.return_value = [ self.mc1 ]
        with self.patch_cs:
            service = Service( self.manager, 'alias', self.config )

        c1, c_m1 = self.CS.call_args_list
        s1, s_m1 = service.collection_services

        self.assertEqual( c1, mock.call( self.manager, self.config, 'alias'))
        self.assertEqual( c_m1, mock.call( s1, self.mc1, 'alias.mc1', 'mc1'))

    def test_config_managed_class_level(self):
        self.manager.direct_plug.return_value = False
        self.manager.get_managed_classes.return_value = [ self.mc2 ]
        with self.patch_cs:
            service = Service( self.manager, 'alias', self.config )

        c1, c_m2, c_m1 = self.CS.call_args_list
        s1, s_m2, s_m1 = service.collection_services

        self.assertEqual( c1, mock.call( self.manager, self.config, 'alias'))
        self.assertEqual( c_m2, mock.call( s1, self.mc2, 'alias.mc2', 'mc2'))
        self.assertEqual( c_m1, mock.call( s_m2, self.mc1, 'alias.mc2.mc1', ''))



