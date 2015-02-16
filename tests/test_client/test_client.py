#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.conf import Conf

try:
    import napix
except ImportError:
    __test__ = False
else:
    from napixd.client.client import Client


class TestClient(unittest.TestCase):
    def test_bad_auth(self):
        self.assertRaises(ValueError, Client, 'server.napix.nx', 'login:pass')
        self.assertRaises(ValueError, Client, 'server.napix.nx', {})

    def test_client_conf(self):
        with mock.patch('napixd.client.client.LoginAuthenticator') as LA:
            Client('server.napix.nx', Conf({'login': 'user', 'key': 'pass'}))
        LA.assert_called_once_with('user', 'pass')

    def test_client_dict(self):
        with mock.patch('napixd.client.client.Connection') as Con:
            with mock.patch('napixd.client.client.LoginAuthenticator') as LA:
                Client('server.napix.nx', {'login': 'user', 'key': 'pass'})
        LA.assert_called_once_with('user', 'pass')
        Con.assert_called_once_with('server.napix.nx', LA.return_value)

    def test_client(self):
        auth = mock.Mock()
        with mock.patch('napixd.client.client.Connection') as Con:
            Client('server.napix.nx', auth)
        Con.assert_called_once_with('server.napix.nx', auth)
