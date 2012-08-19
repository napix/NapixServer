#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest2

from mock.http_client import MockHTTPClient, MockHTTPClientError
from napixd.conf import Conf
from bases import WSGITester

from napixd.plugins import AAAPlugin
from napixd.loader import NapixdBottle

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
                self._make_env('GET', '/test', auth='method=GET&path=/test&host=napix.test:sign' ))
        self.assertEqual( result, '{"access": "granted"}')

    def testBadHost(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='method=GET&path=/test&host=napix.other:sign' ))
        self.assertEqual( status, 403)
        self.assertEqual( result, 'Bad host')

    def testEmptyHost(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='method=GET&path=/test&host=:sign' ))
        self.assertEqual( status, 403)
        self.assertEqual( result, 'No host')

    def testNoHost(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='method=GET&path=/test&hast=napix.test:sign' ))
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

    def testDebugNoauth(self):
        with Conf.get_default().force( 'Napix.debug',True):
            status, headers, result = self._do_request(
                    self._make_env('GET', '/test', auth= False,query='authok'))
        self.assertEqual( status, 200)

    def testNodebugNoAuth(self):
        with Conf.get_default().force( 'Napix.debug',False):
            status, headers, result = self._do_request(
                    self._make_env('GET', '/test', auth= False,query='authok'))
        self.assertEqual( status, 401)

    def testMismatchMethod(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='method=POST&path=/test&host=napix.test:sign' ))
        self.assertEqual( status, 403)
        self.assertEqual( result, 'Bad authorization data')


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
                self._make_env('GET', '/test', auth='method=GET&path=/test&host=napix.test:sign' ))
        self.assertEqual( status, 500)
        self.assertEqual( headers['Content-Type'], 'text/plain')
        self.assertEqual( result, 'Auth server responded unexpected 502 code')

    def testForbidden(self):
        self._install(403)
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='method=GET&path=/test&host=napix.test:sign' ))
        self.assertEqual( status, 403)
        self.assertEqual( headers['Content-Type'], 'text/plain')
        self.assertEqual( result, 'Access Denied')

    def testFailed( self):
        self.bottle.install(AAAPlugin(
            {'auth_url': 'http://auth.napix.local/auth/authorization/' , 'service' : 'napix.test' },
            MockHTTPClientError()))
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='method=GET&path=/test&host=napix.test:sign' ))
        self.assertEqual( status, 500)
        self.assertEqual( headers['Content-Type'], 'text/plain')
        self.assertEqual( result, 'Auth server did not respond')





if __name__ == '__main__':
    unittest2.main()
