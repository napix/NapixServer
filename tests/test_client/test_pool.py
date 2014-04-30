#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

try:
    import gevent
    import napix
except ImportError:
    __test__ = False
else:
    from napixd.client.gevent import Client
    from napixd.client.pool import ClientPool


class TestClientPool(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch_client = mock.patch('napixd.client.pool.Client', spec=Client)
        cls.patch_spawn = mock.patch('gevent.spawn')

    def setUp(self):
        self.auth = mock.Mock()
        self.pool = ClientPool(authenticator=self.auth, simultaneous=3)

        self.Client = self.patch_client.start()
        self.client = self.Client.return_value
        self.client.spec = Client

        self.spawn = self.patch_spawn.start()

        self.greenlet = self.spawn.return_value
        self.greenlet.spec = gevent.Greenlet
        self.greenlet.successful.return_value = True

    def tearDown(self):
        self.patch_client.stop()
        self.patch_spawn.stop()

    def test_client_new(self):
        self.pool.request('server.napix.nx', 'GET', '/')

        self.Client.assert_called_once_with('server.napix.nx', self.auth, simultaneous=3)

    def test_request(self):
        gl = self.pool.request('server.napix.nx', 'GET', '/')
        self.spawn.assert_called_once_with(self.client.request, 'GET', '/')
        self.assertEqual(gl, self.greenlet)

    def test_client_cached(self):
        self.pool.request('server.napix.nx', 'GET', '/abc')
        self.pool.request('server.napix.nx', 'GET', '/def')

        self.assertEqual(self.Client.call_count, 1)

    def test_client_not_cached(self):
        self.pool.request('server1.napix.nx', 'GET', '/abc')
        self.pool.request('server2.napix.nx', 'GET', '/def')

        self.assertEqual(self.Client.call_count, 2)

    def test_wait_unordered(self):
        r1 = self.pool.request('server1.napix.nx', 'GET', '/abc')
        r2 = self.pool.request('server2.napix.nx', 'GET', '/def')
        r3 = self.pool.request('server2.napix.nx', 'GET', '/def')

        with mock.patch('gevent.iwait') as iwait:
            iwait.return_value = [r3, r1, r2]

            iterator = self.pool.wait_unordered()
            self.assertEqual(list(iterator), [r3.value, r1.value, r2.value])

        self.assertEqual(self.pool.wait(), [])

    def test_wait(self):
        r1 = self.pool.request('server1.napix.nx', 'GET', '/abc')
        r2 = self.pool.request('server2.napix.nx', 'GET', '/def')
        r3 = self.pool.request('server2.napix.nx', 'GET', '/def')

        self.assertEqual(self.pool.wait(), [r1.value, r2.value, r3.value])
