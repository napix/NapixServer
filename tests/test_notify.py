#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import unittest2
import mock

from napixd.notify import Notifier
from napixd.conf import Conf
from napixd.client import Client

class RunStop(Exception):
    pass

class TestNotifier( unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = mock.Mock( root_urls= [ 'base' ])
        cls.credentials = mock.Mock()

    def setUp(self):
        with mock.patch('napixd.notify.Client', spec=Client) as client:
            with Conf.get_default().force( 'Napix.notify', {
                'url': 'http://auth.server.nx/notify/',
                'credentials' : self.credentials
                }):
                self.client = client
                self.notifier = Notifier( self.app, 100 )

    def test_client(self):
        self.client.assert_called_once_with( 'auth.server.nx', self.credentials)

    def test_run_normal(self):
        self.client().request().status = 201
        self.client().request().getheader.return_value = '/notify/entity'
        with self.assertRaises( RunStop):
            with mock.patch('napixd.notify.sleep', side_effect=[None, RunStop()]):
                self.notifier.run()
        self.client().request.has_calls(
                mock.call( 'POST', '/notify/', body={
                    'host' : 'server.napix.nx:8002' , 'managers' : [ 'base' ]
                    }),
                mock.call( 'PUT', '/notify/entity', body={
                    'host' : 'server.napix.nx:8002' , 'managers' : [ 'base' ]
                    })
                )

    def test_run_fail(self):
        self.client().request().status = 403
        with mock.patch('napixd.notify.sleep', side_effect=[None, None, None]):
            self.notifier.run()
        self.client().request.has_calls(
                mock.call( 'POST', '/notify/', body={
                    'host' : 'server.napix.nx:8002' , 'managers' : [ 'base' ]
                    }),
                mock.call( 'POST', '/notify/', body={
                    'host' : 'server.napix.nx:8002' , 'managers' : [ 'base' ]
                    }),
                mock.call( 'POST', '/notify/', body={
                    'host' : 'server.napix.nx:8002' , 'managers' : [ 'base' ]
                    }),
                )

