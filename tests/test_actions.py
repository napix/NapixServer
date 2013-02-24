#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest2
from napixd.managers.actions import action, parameter

class TestDecorator( unittest2.TestCase):
    def setUp(self):
        @action
        def send_mail(self, resource, dest, subject='export'):
            pass
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

