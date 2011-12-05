#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest2
from napixd.plugins import AAAPlugin
from napixd.tests.mock.http_client import MockHTTPClient
from napixd.loader import NapixdBottle
from napixd.test.bases import WSGITester

class MockService(object):
    def __init__(self,url = ''):
        self.url = url or 'test'
    def setup_bottle(self,app):
        app.route('/' + self.url, callback = self.serve)
    def serve(self):
        return { 'access': 'granted' }

class TestAAAPluginSuccess(WSGITester):
    def setUp(self):
        self.bottle = NapixdBottle([ MockService() ])
        self.bottle.setup_bottle()
        self.bottle.install(AAAPlugin(
            {'auth_url': 'http://auth.napix.local/auth/authorization/' , 'service' : 'napix.test' },
            MockHTTPClient(200)))

    def testSuccess(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='host=napix.test:sign' ))
        self.assertEqual( result, '{"access": "granted"}')

    def testBadHost(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='host=napix.other:sign' ))
        self.assertEqual( status, 403)
        self.assertEqual( result, 'Bad host')

    def testEmptyHost(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='host=:sign' ))
        self.assertEqual( status, 403)
        self.assertEqual( result, 'No host')

    def testNoHost(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='hast=napix.test:sign' ))
        self.assertEqual( status, 403)
        self.assertEqual( result, 'No host')

    def testNoAuth(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth= False))
        self.assertEqual( status, 401)
        self.assertEqual( result, 'You need to sign your request')

    def testBadAuth(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth= 'lolnetwork' ))
        self.assertEqual( status, 401)
        self.assertEqual( result, 'Incorrect NAPIX Authentication')

class TestAAAPlugin(WSGITester):
    def setUp(self):
        self.bottle = NapixdBottle([ MockService() ])
        self.bottle.setup_bottle()

    def _install(self,status):
        self.bottle.install(AAAPlugin(
            {'auth_url': 'http://auth.napix.local/auth/authorization/' , 'service' : 'napix.test' },
            MockHTTPClient(status)))

    def testError(self):
        self._install(502)
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='host=napix.test:sign' ))
        self.assertEqual( status, 500)
        self.assertEqual( headers['Content-Type'], 'text/plain')
        self.assertEqual( result, 'Auth server responded unexpected 502 code')

    def testForbidden(self):
        self._install(403)
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='host=napix.test:sign' ))
        self.assertEqual( status, 403)
        self.assertEqual( headers['Content-Type'], 'text/plain')
        self.assertEqual( result, 'Access Denied')


if __name__ == '__main__':
    unittest2.main()
