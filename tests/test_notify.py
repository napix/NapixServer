#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import unittest2
import mock
import httplib
import contextlib

from napixd.notify import Notifier
from napixd.client import Client
from napixd.conf import Conf
from napixd.application import NapixdBottle


class RunStop(Exception):
    pass


class TestNotifier(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.patch_client = mock.patch('napixd.notify.Client', **{
            'spec': Client,
            'return_value.spec': Client,
        })
        cls.app = mock.Mock(spec=NapixdBottle)
        cls.app.list_managers.return_value = ['base']
        cls.credentials = mock.Mock()
        cls.uid = mock.patch(
            'napixd.notify.uid', '2550ba7b-aec4-4a67-8047-2ce1ec8ca8ae')
        cls.uid.start()

    @classmethod
    def tearDownClass(cls):
        cls.uid.stop()

    def setUp(self):
        with self.patch_client as Client_:
            self.Client = Client_
            self.client = Client_.return_value
            self.client.request.return_value = mock.Mock(
                spec=httplib.HTTPResponse, status=200, reason='OK')
            self.notifier = Notifier(self.app, Conf({
                'url': 'http://auth.server.nx/notify/',
                'credentials': self.credentials
            }), 'server.napix.io', 'server.napix.nx:8002',
                u'The base Napix server')

    notify_create = mock.call('POST', '/notify/', body={
        'uid': '2550ba7b-aec4-4a67-8047-2ce1ec8ca8ae',
        'host': 'server.napix.nx:8002',
        'service': 'server.napix.io',
        'managers': ['base'],
        'description': u'The base Napix server'
    })
    notify_update = mock.call('PUT', '/notify/entity', body={
        'uid': '2550ba7b-aec4-4a67-8047-2ce1ec8ca8ae',
        'host': 'server.napix.nx:8002',
        'managers': ['base'],
        'service': 'server.napix.io',
        'description': u'The base Napix server'
    })

    def test_client(self):
        self.Client.assert_called_once_with('auth.server.nx', self.credentials)

    def test_run_normal(self):
        self.client.request.return_value.status = 201
        self.client.request.return_value.getheader.return_value = '/notify/entity'
        with contextlib.nested(
                self.assertRaises(RunStop),
                mock.patch('napixd.notify.sleep', side_effect=[None, RunStop()])):
            self.notifier.run()

        self.assertEqual(self.client.request.call_args_list, [
            self.notify_create,
            self.notify_update
        ])

    def test_run_fail(self):
        self.client.request.return_value.status = 403
        with mock.patch('napixd.notify.sleep', side_effect=[None, None, None]):
            self.notifier.run()

        self.assertEqual(self.client.request.call_args_list, [
            self.notify_create,
            self.notify_create,
            self.notify_create
        ])
