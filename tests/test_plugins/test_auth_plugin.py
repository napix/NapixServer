#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import socket
import httplib
import unittest2
import mock

import bottle

from permissions.models import Perm
from permissions.managers import PermSet

from napixd.plugins.auth import (
    AAAPlugin, AAAChecker,
    Success, Fail,
    TimeMixin, NoSecureMixin, AutonomousMixin,
    get_auth_plugin
)


class TestAAAPluginHostCheck(unittest2.TestCase):

    def test_no_host(self):
        plugin = AAAPlugin({
            'auth_url': 'http://auth.napix.local/auth/authorization/',
        },
            service_name='org.napix.test'
        )

        with mock.patch('bottle.request', method='GET', path='/a/b', query_string=''):
            check = plugin.host_check({
                'host': 'a.b.c',
                'method': 'GET',
                'path': '/a/b'
            })
        self.assertEqual(check, None)


class AAAPluginBase(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.patch_aaachecker = mock.patch(
            'napixd.plugins.auth.AAAChecker', spec=AAAChecker)

    def setUp(self, status):
        self.AAAchecker = self.patch_aaachecker.start()
        self.AAAchecker.return_value.authserver_check.return_value = Success(
            None) if status == 200 else Fail(None)

        plugin = AAAPlugin({
            'auth_url': 'http://auth.napix.local/auth/authorization/',
            'hosts': ['napix.test'],
        },
            service_name='org.napix.test'
        )
        self.success = mock.MagicMock(__name__='my_callback')
        self.cb = plugin.apply(self.success, None)

    def tearDown(self):
        self.patch_aaachecker.stop()

    def _do_request(self, method, url, auth=None, query=''):
        env = {
            'REMOTE_ADDR': '1.2.3.4',
        }
        headers = {}
        if auth:
            headers['Authorization'] = auth
        env = mock.patch('bottle.request', method=method, path=url,
                         query_string=query,
                         GET={query: ''},
                         environ=env, headers=headers,
                         )

        with env:
            try:
                return self.cb()
            except bottle.HTTPError as e:
                return e


class TestAAAPluginSuccess(AAAPluginBase):

    def setUp(self):
        super(TestAAAPluginSuccess, self).setUp(200)

    def testSuccess(self):
        resp = self._do_request(
            'GET', '/', auth='method=GET&path=/&host=napix.test:sign')
        self.success.assert_called_once_with()
        self.assertEqual(resp, self.success.return_value)

    def test_success_escape(self):
        resp = self._do_request(
            'GET', '/a%20b', auth='method=GET&path=%2Fa%2520b&host=napix.test:sign')
        self.success.assert_called_once_with()
        self.assertEqual(resp, self.success.return_value)

    def test_success_filter_get_all(self):
        pset = mock.Mock(spec=PermSet)
        pset.filter_paths.return_value = ['/a/d']
        self.AAAchecker.return_value.authserver_check.return_value = mock.Mock(
            spec=Success, content=pset)
        self.success.return_value = {
            '/a/b': {'a': 1},
            '/a/d': {'a': 2},
        }
        resp = self._do_request(
            'GET', '/', auth='method=GET&path=/&host=napix.test:sign')

        self.success.assert_called_once_with()
        self.assertEqual(resp, {'/a/d': {'a': 2}})
        pset.filter_paths.assert_called_once_with(
            'org.napix.test', {
                '/a/b': {'a': 1},
                '/a/d': {'a': 2},
            })

    def test_success_filter(self):
        pset = mock.Mock(spec=PermSet)
        pset.filter_paths.return_value = ['/a/d']
        self.AAAchecker.return_value.authserver_check.return_value = mock.Mock(
            spec=Success, content=pset)
        self.success.return_value = ['/a/b', '/a/d']
        resp = self._do_request(
            'GET', '/', auth='method=GET&path=/&host=napix.test:sign')

        self.success.assert_called_once_with()
        self.assertEqual(resp, ['/a/d'])
        pset.filter_paths.assert_called_once_with(
            'org.napix.test', ['/a/b', '/a/d'])

    def testBadHost(self):
        response = self._do_request(
            'GET', '/test', auth='method=GET&path=/test&host=napix.other:sign')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.body, 'Bad host')

    def testEmptyHost(self):
        response = self._do_request(
            'GET', '/test', auth='method=GET&path=/test&host=:sign')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.body, 'Missing authentication data: \'host\'')

    def testNoHost(self):
        response = self._do_request(
            'GET', '/test', auth='method=GET&path=/test&hast=napix.test:sign')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.body, 'Missing authentication data: \'host\'')

    def testNoAuth(self):
        response = self._do_request('GET', '/test', auth=False)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.body, 'You need to sign your request')


class TestAAAPluginBypass(AAAPluginBase):

    def setUp(self):
        super(TestAAAPluginBypass, self).setUp(403)

    def testBadAuth(self):
        response = self._do_request('GET', '/test', auth='lolnetwork')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.body, 'Incorrect NAPIX Authentication')

    def testMismatchMethod(self):
        response = self._do_request(
            'GET', '/test', auth='method=POST&path=/test&host=napix.test:sign')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.body, 'Bad authorization data method does not match')


class TestAAAPluginDenied(AAAPluginBase):

    def setUp(self):
        super(TestAAAPluginDenied, self).setUp(403)

    def testForbidden(self):
        response = self._do_request(
            'GET', '/test', auth='method=GET&path=/test&host=napix.test:sign')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.body, 'Access Denied')

    def test_deny_commont_root(self):
        self.AAAchecker.return_value.authserver_check.return_value = Fail(['/a/', '/b/'])
        response = self._do_request(
            'GET', '/', auth='method=GET&path=/&host=napix.test:sign')
        self.assertEqual(response.status_code, 203)
        self.assertEqual(response.body, ['/a/', '/b/'])


class _TestAAAChecker(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.con = mock.patch(
            'napixd.plugins.auth.httplib.HTTPConnection', spec=httplib.HTTPConnection)

    def setUp(self):
        self.Connection = self.con.start()
        self.connection = self.Connection.return_value
        self.response = self.connection.getresponse.return_value
        self.response.status = 200

        self.checker = AAAChecker('auth.napix.local', '/auth/authorization/')

    def tearDown(self):
        self.con.stop()


class TestAAACheckerSuccess(_TestAAAChecker):

    def testSuccess(self):
        self.assertTrue(self.checker.authserver_check({'path': '/test'}))
        self.Connection.assert_called_once_with('auth.napix.local', timeout=5)
        self.connection.request.assert_called_once_with(
            'POST', '/auth/authorization/',
            body='''{"path": "/test"}''', headers={
                'Accept': 'application/json',
                'Content-type': 'application/json', })

    def test_not_generate_permset(self):
        self.response.getheader.return_value = ''
        self.assertTrue(self.checker.authserver_check({'path': '/test'}))

    def test_generate_permset_empty(self):
        self.response.read.return_value = '[]'
        self.response.getheader.return_value = 'application/json'
        check = self.checker.authserver_check({'path': '/test'})

        self.assertTrue(isinstance(check, Success))
        self.assertEqual(check.content, None)

    def test_generate_permset(self):
        self.response.read.return_value = '[{"host":"*","methods":["GET"],"path":"/a/b"}]'
        self.response.getheader.return_value = 'application/json'
        check = self.checker.authserver_check({'path': '/test'})

        self.assertTrue(isinstance(check, Success))
        permset = check.content
        self.assertEqual(len(permset), 1)
        self.assertTrue(Perm('*', 'GET', '/a/b') in permset)


class TestAAACheckerFail(_TestAAAChecker):

    def testFail(self):
        self.response.status = 403
        self.assertFalse(self.checker.authserver_check({'path': '/test'}))

    def testError(self):
        self.response.status = 504
        self.assertRaises(
            bottle.HTTPError, self.checker.authserver_check, {'path': '/test'})

    def testSocketError(self):
        self.connection.getresponse.side_effect = socket.error('unclean pipe')
        self.assertRaises(
            bottle.HTTPError, self.checker.authserver_check, {'path': '/test'})


class _MockAAAPlugin(object):
    def __init__(self, settings, service_name):
        self.settings = settings
        self.logger = mock.Mock()
        self.witness = mock.Mock()
        self.witness.authorization_extract.return_value = {
            'method': 'GET',
            'path': '/',
            'login': 'login',
            'signature': 'sign'
        }

    def authserver_check(self, content):
        return self.witness.authserver_check(content)

    def authorization_extract(self, request):
        return self.witness.authorization_extract(request)

    def host_check(self, content):
        return self.witness.host_check(content)

    def reject(self, reason):
        raise Exception(reason)


class MockAAAPlugin(NoSecureMixin, _MockAAAPlugin):
    pass


class TestNoSecurePugin(unittest2.TestCase):
    def setUp(self):
        self.nsp = MockAAAPlugin({
        }, 'server.napix.io')
        self.GET = {}
        self.request = mock.Mock(GET=self.GET)

    def test_authorisation_extract_no_token(self):
        self.assertEqual(self.nsp.authorization_extract(self.request), {
            'method': 'GET',
            'path': '/',
            'login': 'login',
            'signature': 'sign',
            'is_secure': True,
        })

    def test_authorisation_extract_misformated(self):
        self.GET['token'] = 'master,sign'
        self.assertRaises(Exception, self.nsp.authorization_extract, self.request)

    def test_authorisation_extract(self):
        self.GET['token'] = 'master:sign'
        self.assertEqual(self.nsp.authorization_extract(self.request), {
            'method': self.request.method,
            'path': self.request.path,
            'login': 'master',
            'signature': 'sign',
            'is_secure': False,
            'msg': 'master',
        })

    def test_host_check_not_secure(self):
        self.assertTrue(self.nsp.host_check({'is_secure': False}))

    def test_host_check_secure(self):
        self.assertTrue(self.nsp.host_check({'is_secure': True}),
                        self.nsp.witness.host_check.return_value)


class MockAutonomousPlugin(AutonomousMixin, _MockAAAPlugin):
    pass


class TestAutonmousMixin(unittest2.TestCase):
    def setUp(self):
        self.nsp = MockAutonomousPlugin({
            'password': 'key'
        }, 'server.napix.io')
        self.GET = {}
        self.request = mock.Mock(GET=self.GET)

    def test_authserver_check(self):
        with mock.patch.object(self.nsp, 'sign', return_value='sign') as sign:
            self.assertTrue(isinstance(self.nsp.authserver_check({
                'login': 'local_master',
                'msg': 'msg',
                'signature': 'sign'
            }), Success))
            sign.assert_called_once_with('msg')

    def test_authserver_check_bad_sign(self):
        with mock.patch.object(self.nsp, 'sign', return_value='sign'):
            self.assertTrue(isinstance(self.nsp.authserver_check({
                'login': 'local_master',
                'msg': 'msg',
                'signature': 'bad'
            }), Fail))


class TestGetClass(unittest2.TestCase):
    def test_get_no_options(self):
        cls = get_auth_plugin(False, False)
        self.assertTrue(issubclass(cls, AAAPlugin))
        self.assertTrue(issubclass(cls, NoSecureMixin))
        self.assertFalse(issubclass(cls, TimeMixin))

    def test_get_options(self):
        cls = get_auth_plugin(True, True)
        self.assertTrue(issubclass(cls, AAAPlugin))
        self.assertFalse(issubclass(cls, NoSecureMixin))
        self.assertTrue(issubclass(cls, TimeMixin))
