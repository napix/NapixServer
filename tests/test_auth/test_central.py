#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import unittest
import mock

import httplib
import socket

from napixd.conf import Conf
from napixd.http.request import Request
from napixd.http.response import HTTPError

try:
    from permissions.managers import PermSet
except ImportError:
    __test__ = False
else:
    from napixd.auth.central import CentralAuthProvider, Filter


class TestFilter(unittest.TestCase):
    def setUp(self):
        self.rules = rules = mock.Mock(spec=PermSet)
        rules.filter_paths.return_value = ['/x/abc', '/x/def']
        self.filter = Filter(rules)

    def test_filter_list(self):
        f = self.filter(['/x/abc', '/x/def', '/x/ghi'])
        self.rules.filter_paths.assert_called_once_with(['/x/abc', '/x/def', '/x/ghi'])
        self.assertEqual(f, ['/x/abc', '/x/def'])

    def test_filter_dict(self):
        f = self.filter({
            '/x/abc': 1,
            '/x/def': 2,
            '/x/ghi': 3,
        })
        self.assertEqual(f, {
            '/x/abc': 1,
            '/x/def': 2,
        })


class TestCentralAuthProviderBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch_con = mock.patch('httplib.HTTPConnection') 

    def setUp(self):
        self.Con = self.patch_con.start()

    def tearDown(self):
        self.patch_con.stop()

    def test_from_settings(self):
        cap = CentralAuthProvider.from_settings('service.name', Conf({
            'url': u'http://new.url/abc/def',
            'auth_url': u'http://old.url/abc/ghi',
        }))
        self.assertEqual(cap.url, '/abc/def')
        self.assertEqual(cap.http_client, self.Con.return_value)

    def test_from_settings_old(self):
        cap = CentralAuthProvider.from_settings('service.name', Conf({
            'auth_url': u'http://old.url/abc/ghi',
        }))
        self.assertEqual(cap.url, '/abc/ghi')


class TestCentralAuthProvider(unittest.TestCase):
    def setUp(self):
        self.connection = con = mock.Mock(httplib.HTTPConnection)
        self.response = self.connection.getresponse.return_value
        self.response.status = 200

        self.filter_factory = ff = mock.Mock()
        self.checker = CentralAuthProvider(con, '/auth/authorization/', ff)

        self.request = mock.Mock(spec=Request, path='/abc/', method='GET')
        self.content = {
            'authorization': 1
        }

    def call(self):
        return self.checker(self.request, self.content)

    def test_success(self):
        self.request.path = '/abc/def'
        self.assertTrue(self.call() is True)
        self.connection.request.assert_called_once_with(
            'POST', '/auth/authorization/',
            body='''{"authorization": 1}''', headers={
                'Accept': 'application/json',
                'Content-type': 'application/json',
            })

    def test_fail_but_success(self):
        self.request.path = '/abc/'
        self.response.status = 403
        self.response.read.return_value = '[{"host":"*","methods":["GET"],"path":"/a/*"}]'
        self.response.getheader.return_value = 'application/json'

        check = self.call()

        self.assertEqual(check, self.filter_factory.return_value)
        self.filter_factory.assert_called_once_with([{
            'host': '*',
            'methods': ['GET'],
            'path': '/a/*',
        }])

    def test_fail_and_203(self):
        self.request.path = '/abc/'
        self.response.status = 403
        self.response.read.return_value = '[{"host":"*","methods":["GET"],"path":"/a/b"}]'
        self.response.getheader.return_value = 'application/json'

        try:
            self.call()
        except HTTPError as resp:
            self.assertEqual(resp.body, ['/a/b'])
        else:
            self.fail()

    def test_fail(self):
        self.request.path = '/abc/def'
        self.response.status = 403
        self.assertTrue(self.call() is False)

    def test_error(self):
        self.response.status = 504
        self.assertRaises(HTTPError, self.call)

    def test_socket_error(self):
        self.connection.getresponse.side_effect = socket.error('unclean pipe')
        self.assertRaises(HTTPError, self.call)

    def test_generate_permset_empty(self):
        self.response.read.return_value = '[]'
        self.response.getheader.return_value = 'application/json'
        check = self.call()

        self.assertEqual(check, self.filter_factory.return_value)
        self.filter_factory.assert_called_once_with([])

    def test_generate_permset(self):
        self.response.read.return_value = '[{"host":"*","methods":["GET"],"path":"/a/b"}]'
        self.response.getheader.return_value = 'application/json'
        check = self.call()

        self.assertEqual(check, self.filter_factory.return_value)
        self.filter_factory.assert_called_once_with([{
            'host': '*',
            'methods': ['GET'],
            'path': '/a/b',
        }])
