#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest2

from mock.http_client import FakeCheckerFactory, FakeHTTPClientFactory, FakeHTTPErrorClient
from bases import WSGITester

import bottle
from bottle import Bottle

from napixd.plugins import AAAPlugin, AAAChecker, ConversationPlugin


class AAAPluginBase(WSGITester):
    def setUp(self):
        self.bottle = Bottle( catchall=False)
        self.bottle.install( ConversationPlugin());
        @self.bottle.route( '/test')
        def ok():
            return { 'access' : 'granted' }
    def _install(self,status, allow_bypass=False):
        self.bottle.install(AAAPlugin(
            {'auth_url': 'http://auth.napix.local/auth/authorization/' , 'service' : 'napix.test' },
            allow_bypass=allow_bypass,
            auth_checker_factory = FakeCheckerFactory(status, self)))

class TestAAAPluginSuccess(AAAPluginBase):
    def setUp(self):
        super( TestAAAPluginSuccess, self).setUp()
        self._install( 200)

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
        self.assertEqual( result, 'Missing authentication data: \'host\'')

    def testNoHost(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='method=GET&path=/test&hast=napix.test:sign' ))
        self.assertEqual( status, 403)
        self.assertEqual( result, 'Missing authentication data: \'host\'')

    def testNoAuth(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth= False))
        self.assertEqual( status, 401)
        self.assertEqual( result, 'You need to sign your request')

    def testNodebugNoAuth(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth= False,query='authok'))
        self.assertEqual( status, 401)

class TestAAAPluginByPass(AAAPluginBase):
    def setUp(self):
        super( TestAAAPluginByPass, self).setUp()
        self._install( 403, True)

    def testBadAuth(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth= 'lolnetwork' ))
        self.assertEqual( status, 401)
        self.assertEqual( result, 'Incorrect NAPIX Authentication')

    def testDebugNoauth(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth= False,query='authok'))
        self.assertEqual( status, 200)

    def testMismatchMethod(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='method=POST&path=/test&host=napix.test:sign' ))
        self.assertEqual( status, 403)
        self.assertEqual( result, 'Bad authorization data')

class TestAAAPluginDenied(AAAPluginBase):
    def testForbidden(self):
        self._install(403)
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='method=GET&path=/test&host=napix.test:sign' ))
        self.assertEqual( status, 403)
        self.assertEqual( headers['Content-Type'], 'text/plain')
        self.assertEqual( result, 'Access Denied')

class TestAAAChecker(unittest2.TestCase):
    def _install(self, code):
        self.checker = AAAChecker( 'auth.napix.local', '/auth/authorization/',
                http_factory=FakeHTTPClientFactory( code, self)  )
    def testSuccess( self):
        self._install( 200)
        self.assertTrue( self.checker.authserver_check({ 'path': '/test' }))
    def testFail( self):
        self._install( 403)
        self.assertFalse( self.checker.authserver_check({ 'path': '/test' }))

    def testError( self):
        self._install( 504)
        self.assertRaises( bottle.HTTPError, self.checker.authserver_check, { 'path': '/test' })

    def testSocketError(self):
        self.checker = AAAChecker(  'auth.napix.local', '/auth/authorization/',
                http_factory=FakeHTTPErrorClient)
        self.assertRaises( bottle.HTTPError, self.checker.authserver_check, { 'path': '/test' })

