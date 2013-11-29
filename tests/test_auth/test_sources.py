#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

from napixd.auth.sources import SecureAuthProtocol, NonSecureAuthProtocol
from napixd.http.request import Request
from napixd.http.response import HTTPError


class TestNotSecureProtocol(unittest.TestCase):
    def setUp(self):
        self.GET = {}
        self.request = mock.Mock(spec=Request, GET=self.GET)
        self.nsp = NonSecureAuthProtocol('token')

    def call(self):
        return self.nsp(self.request)

    def test_extract_no_token(self):
        self.assertEqual(self.call(), None)

    def test_extract_misformated(self):
        self.GET['token'] = 'master,sign'
        self.assertRaises(HTTPError, self.call)

    def test_extract(self):
        self.GET['token'] = 'master:sign'
        self.assertEqual(self.call(), {
            'login': 'master',
            'signature': 'sign',
            'is_secure': False,
            'msg': 'master',
        })


class TestSecureProtocol(unittest.TestCase):
    def setUp(self):
        self.headers = {
            'Authorization': 'login=root&nonce=123abc&method=GET&path=/&host=server.napix.nx:sign'
        }
        self.request = mock.Mock(spec=Request,
                                 headers=self.headers,
                                 path='/',
                                 query_string='',
                                 method='GET')
        self.sp = SecureAuthProtocol()

    def call(self):
        return self.sp(self.request)

    def test_no_header(self):
        self.headers.pop('Authorization')
        self.assertTrue(self.call() is None)

    def test_misformated(self):
        self.headers['Authorization'] = 'this & that'
        self.assertRaises(HTTPError, self.call)

    def test_missing_keys(self):
        self.headers['Authorization'] = 'path=/&host=server.napix.nx:sign'
        self.assertRaises(HTTPError, self.call)

    def test_extract(self):
        self.assertEqual(self.call(), {
            'host': 'server.napix.nx',
            'login': 'root',
            'method': 'GET',
            'msg': 'login=root&nonce=123abc&method=GET&path=/&host=server.napix.nx',
            'nonce': '123abc',
            'path': '/',
            'signature': 'sign'
        })
