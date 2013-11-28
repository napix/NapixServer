#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
import mock

from napixd.auth.request import HostChecker, RequestParamaterChecker
from napixd.http.response import HTTPError
from napixd.http.request import Request


class TestHostChecker(unittest.TestCase):
    def setUp(self):
        self.hc = HostChecker(['this.napix.io', 'that.napix.io'])
        self.headers = {'host': 'this.napix.io'}
        self.request = mock.Mock(spec=Request, headers=self.headers)
        self.content = {'host': 'this.napix.io'}

    def call(self):
        return self.hc(self.request, self.content)

    def test_in_host(self):
        self.assertTrue(self.call() is None)

    def test_out_host(self):
        self.headers['host'] = self.content['host'] = 'this.napix.com'
        self.assertRaises(HTTPError, self.call)

    def test_mismatch(self):
        self.content['host'] = 'this.napix.com'
        self.assertRaises(HTTPError, self.call)


class TestRequestParameterChecker(unittest.TestCase):
    def setUp(self):
        self.rpc = RequestParamaterChecker()
        self.request = mock.Mock(spec=Request, path='/abc', method='GET', query_string='')
        self.content = {
            'path': '/abc',
            'method': 'GET',
        }

    def call(self):
        return self.rpc(self.request, self.content)

    def test_ok(self):
        self.assertTrue(self.call() is None)

    def test_mismatch(self):
        self.request.method = 'POST'
        self.assertRaises(HTTPError, self.call)

    def test_query_string_ok(self):
        self.content['path'] += '?mpm=prefork'
        self.request.query_string = 'mpm=prefork'
        self.assertTrue(self.call() is None)

    def test_query_string_mismatch(self):
        self.content['path'] += '?mpm=prefork'
        self.request.query_string = 'mpm=worker'
        self.assertRaises(HTTPError, self.call)
