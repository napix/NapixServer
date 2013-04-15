#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import socket
import httplib
import unittest2
import mock

import bottle

from permissions.models import Perm

from napixd.plugins.auth import AAAPlugin, AAAChecker

class AAAPluginBase( unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch_aaachecker = mock.patch('napixd.plugins.auth.AAAChecker', spec=AAAChecker)

    def setUp(self, status, allow_bypass=False):
        self.AAAchecker = self.patch_aaachecker.start()
        self.AAAchecker.return_value.authserver_check.return_value = status == 200

        plugin = AAAPlugin({
            'auth_url': 'http://auth.napix.local/auth/authorization/' ,
            'service' : 'napix.test'
            },
            allow_bypass=allow_bypass
            )
        self.cb = plugin.apply( self.success, None)

    def tearDown(self):
        self.patch_aaachecker.stop()

    def success(self):
        return ( 200, {}, 'ok')

    def _make_env( self, method, url, auth=None, query=''):
        env = {
                'REMOTE_ADDR': '1.2.3.4',
                }
        headers = { }
        if auth:
            headers['Authorization'] = auth
        return mock.Mock( method=method, path=url,
                query_string=query,
                GET={ query : '' },
                environ=env, headers=headers,
                )

    def _do_request( self, env):
        with mock.patch( 'bottle.request', env):
            try:
                return self.cb()
            except bottle.HTTPError as e:
                return e.status_code, e.headers, e.body

class TestAAAPluginSuccess(AAAPluginBase):
    def setUp(self):
        super( TestAAAPluginSuccess, self).setUp( 200)

    def testSuccess(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='method=GET&path=/test&host=napix.test:sign' ))
        self.assertEqual( result, 'ok')

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
                self._make_env('GET', '/test', auth= False, query='authok'))
        self.assertEqual( status, 401)

class TestAAAPluginBypass(AAAPluginBase):
    def setUp(self):
        super( TestAAAPluginBypass, self).setUp( 403, allow_bypass=True)

    def testBadAuth(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='lolnetwork' ))
        self.assertEqual( status, 401)
        self.assertEqual( result, 'Incorrect NAPIX Authentication')

    def testDebugNoauth(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth=False, query='authok'))
        self.assertEqual( status, 200)

    def testMismatchMethod(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='method=POST&path=/test&host=napix.test:sign' ))
        self.assertEqual( status, 403)
        self.assertEqual( result, 'Bad authorization data')

class TestAAAPluginDenied(AAAPluginBase):
    def setUp( self):
        super( TestAAAPluginDenied, self).setUp( 403)

    def testForbidden(self):
        status, headers, result = self._do_request(
                self._make_env('GET', '/test', auth='method=GET&path=/test&host=napix.test:sign' ))
        self.assertEqual( status, 403)
        self.assertEqual( result, 'Access Denied')

class _TestAAAChecker(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con = mock.patch( 'napixd.plugins.auth.httplib.HTTPConnection', spec=httplib.HTTPConnection)
        cls.patch_request = mock.patch( 'bottle.request', permissions=None)

    def setUp(self):
        self.request = self.patch_request.start()

        self.Connection = self.con.start()
        self.connection = self.Connection.return_value
        self.response = self.connection.getresponse.return_value
        self.response.status = 200

        self.checker = AAAChecker( 'auth.napix.local', '/auth/authorization/')

    def tearDown( self):
        self.con.stop()
        self.patch_request.stop()

class TestAAACheckerSuccess(_TestAAAChecker):
    def testSuccess( self):
        self.assertTrue( self.checker.authserver_check({ 'path': '/test' }))
        self.Connection.assert_called_once_with( 'auth.napix.local')
        self.connection.request.assert_called_once_with( 'POST', '/auth/authorization/',
                body='''{"path": "/test"}''', headers={
                    'Accept':'application/json',
                    'Content-type':'application/json', })

    def test_not_generate_permset(self):
        self.response.getheader.return_value = ''
        self.checker.authserver_check({ 'path': '/test' })

        self.assertTrue( self.request.permissions is None)

    def test_generate_permset_empty(self):
        self.response.read.return_value = '[]'
        self.response.getheader.return_value = 'application/json'
        self.checker.authserver_check({ 'path': '/test' })

        self.assertFalse( self.request.permissions is None)
        self.assertEqual( len( self.request.permissions), 0)

    def test_generate_permset(self):
        self.response.read.return_value = '[ { "host": "*", "methods" : [ "GET"], "path" : "/a/b" } ]'
        self.response.getheader.return_value = 'application/json'
        self.checker.authserver_check({ 'path': '/test' })

        self.assertEqual( len( self.request.permissions), 1)
        self.assertTrue( Perm( '*', 'GET', '/a/b') in self.request.permissions)

class TestAAACheckerFail( _TestAAAChecker):
    def testFail(self):
        self.response.status = 403
        self.assertFalse( self.checker.authserver_check({ 'path': '/test' }))

    def testError( self):
        self.response.status = 504
        self.assertRaises( bottle.HTTPError, self.checker.authserver_check, { 'path': '/test' })

    def testSocketError(self):
        self.connection.getresponse.side_effect = socket.error('unclean pipe')
        self.assertRaises( bottle.HTTPError, self.checker.authserver_check, { 'path': '/test' })

