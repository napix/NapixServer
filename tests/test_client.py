#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.client import Client
from napixd.conf import Conf


class TestClient(unittest.TestCase):
    def test_bad_auth(self):
        self.assertRaises(ValueError, Client, 'server.napix.nx', 'login:pass')
        self.assertRaises(ValueError, Client, 'server.napix.nx', {})

    def test_client_conf(self):
        with mock.patch('napixd.client.LoginAuthenticator') as LA:
            Client('server.napix.nx', Conf({'login': 'user', 'key': 'pass'}))
        LA.assert_called_once_with('user', 'pass')

    def test_client_dict(self):
        with mock.patch('napixd.client.Connection') as Con:
            with mock.patch('napixd.client.LoginAuthenticator') as LA:
                Client('server.napix.nx', {'login': 'user', 'key': 'pass'})
        LA.assert_called_once_with('user', 'pass')
        Con.assert_called_once_with(
            'server.napix.nx', LA.return_value, follow=False)

    def test_client(self):
        auth = mock.Mock()
        with mock.patch('napixd.client.Connection') as Con:
            Client('server.napix.nx', auth)
        Con.assert_called_once_with('server.napix.nx', auth, follow=False)
