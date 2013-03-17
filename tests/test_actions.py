#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest2
import mock

from napixd.conf import Conf
from napixd.managers.base import ManagerType, Manager
from napixd.managers.actions import action, parameter
from napixd.services import FirstCollectionService
from napixd.services.servicerequest import ServiceActionRequest

class TestDecorator( unittest2.TestCase):
    def setUp(self):
        @action
        def send_mail(self, resource, dest, subject='export'):
            """send a mail"""
            return dest, subject
        self.fn = send_mail

    def test_decorated(self):
        self.assertTrue( self.fn._napix_action)
    def test_parameters(self):
        self.assertListEqual( self.fn.mandatory, ['dest' ])
        self.assertDictEqual( self.fn.optional, { 'subject' :'export' })
    def test_resource_fields(self):
        self.assertDictEqual( self.fn.resource_fields, {
            'dest': {
                'example':'', 'description':''
                },
            'subject': {
                'example':'', 'description':'', 'optional': True
                }
            })
    def test_parameter(self):
        fn = parameter( 'dest', example='you@mail.com')(self.fn)
        self.assertEqual( fn.resource_fields['dest']['example'], 'you@mail.com')

class TestManagerAction( TestDecorator):
    def setUp(self):
        super( TestManagerAction, self).setUp()
        self.manager = ManagerType( 'NewManager', ( Manager, ), {
            'send_mail': self.fn,
            'get_resource' : mock.Mock(spec=True, return_value={ 'mpm': 'prefork' }),
            })
    def test_class_with_views(self):
        self.assertEqual( self.manager.get_all_actions(), [ self.fn ])

class TestServiceAction( TestManagerAction):
    def setUp( self):
        super( TestServiceAction, self).setUp()
        self.cs = FirstCollectionService( self.manager, Conf(), 'my-mock')

    def test_set_bottle(self):
        bottle = mock.Mock()
        self.cs.setup_bottle( bottle)
        self.assertSetEqual(set( mc[0][0] for mc in bottle.route.call_args_list ),
                set([
                    '/my-mock',
                    '/my-mock/',
                    '/my-mock/:f0',
                    '/my-mock/_napix_help',
                    '/my-mock/_napix_resource_fields',
                    '/my-mock/:f0/_napix_all_actions',
                    '/my-mock/:f0/_napix_action/send_mail',
                    '/my-mock/:f0/_napix_action/send_mail/_napix_help',
                    ]))

    def test_all_action(self):
        all_actions = self.cs.as_list_actions('id')
        self.assertEqual( all_actions, [ 'send_mail' ])

