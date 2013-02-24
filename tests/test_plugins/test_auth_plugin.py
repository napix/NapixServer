#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import socket
import httplib
import unittest2
import mock
import bottle

from napixd.plugins import AAAPlugin, AAAChecker

class AAAPluginBase( unittest2.TestCase):
    def setUp(self, status, allow_bypass=False):
        self.AAAChecker = mock.patch('napixd.plugins.AAAChecker', spec=AAAChecker, **{
            'authserver_check.return_value' : status == 200
            })
        self.aaa_checker = self.AAAChecker.start()
        plugin = AAAPlugin({
            'auth_url': 'http://auth.napix.local/auth/authorization/' ,
            'service' : 'napix.test'
            },
            allow_bypass=allow_bypass
            )
        self.cb = plugin.apply( self.success, None)

    def tearDown(self):
        self.AAAChecker.stop()

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
    def setUp(self, status, exc=None):
        self.con = mock.patch( 'napixd.plugins.HTTPConnection', spec=httplib.HTTPConnection, **{
            'getresponse.return_value.status': status,
            'getresponse.side_effect' : exc,
            })
        self.connection = self.con.start()
        self.checker = AAAChecker( 'auth.napix.local', '/auth/authorization/')

    def tearDown( self):
        self.con.stop()

class TestAAACheckerSuccess(_TestAAAChecker):
    def setUp(self):
        super( TestAAACheckerSuccess, self).setUp( 200)
    def testSuccess( self):
        self.assertTrue( self.checker.authserver_check({ 'path': '/test' }))
        self.connection.assert_called_once_with( 'auth.napix.local')
        self.connection().request.assert_called_once_with( 'POST', '/auth/authorization/',
                body='''{"path": "/test"}''', headers={
                    'Accept':'application/json',
                    'Content-type':'application/json', })

class TestAAACheckerFail( _TestAAAChecker):
    def setUp(self):
        super( TestAAACheckerFail, self).setUp( 403)

    def testFail(self):
        self.assertFalse( self.checker.authserver_check({ 'path': '/test' }))

class TestAAACheckerError( _TestAAAChecker):
    def setUp(self):
        super( TestAAACheckerError, self).setUp( 504)
    def testError( self):
        self.assertRaises( bottle.HTTPError, self.checker.authserver_check, { 'path': '/test' })

class TestAAACheckerSockerError( _TestAAAChecker):
    def setUp(self):
        super( TestAAACheckerSockerError, self).setUp( None, socket.error('unclean pipe') )
    def testSocketError(self):
        self.assertRaises( bottle.HTTPError, self.checker.authserver_check, { 'path': '/test' })

