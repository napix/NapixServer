#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import socket
import httplib
import unittest
import mock

from permissions.models import Perm

from napixd.conf import Conf
from napixd.http.request import Request
from napixd.http.response import HTTPError

from napixd.plugins.auth import (
    AAAPlugin, AAAChecker,
    Success, Fail,
    TimeMixin, NoSecureMixin, AutonomousMixin,
    get_auth_plugin
)


class TestAAAChecker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con = mock.patch('napixd.plugins.auth.httplib.HTTPConnection',
                             spec=httplib.HTTPConnection)

    def setUp(self):
        self.Connection = self.con.start()
        self.connection = self.Connection.return_value
        self.response = self.connection.getresponse.return_value
        self.response.status = 200

        self.checker = AAAChecker('auth.napix.local', '/auth/authorization/')

    def tearDown(self):
        self.con.stop()

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

    def testFail(self):
        self.response.status = 403
        self.assertFalse(self.checker.authserver_check({'path': '/test'}))

    def testError(self):
        self.response.status = 504
        self.assertRaises(HTTPError, self.checker.authserver_check, {'path': '/test'})

    def testSocketError(self):
        self.connection.getresponse.side_effect = socket.error('unclean pipe')
        self.assertRaises(HTTPError, self.checker.authserver_check, {'path': '/test'})


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

    def host_check(self, request, content):
        return self.witness.host_check(request, content)

    def reject(self, reason):
        raise Exception(reason)


class MockAAAPlugin(NoSecureMixin, _MockAAAPlugin):
    pass


class TestNoSecurePugin(unittest.TestCase):
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
        self.assertTrue(self.nsp.host_check(self.request, {'is_secure': False}))

    def test_host_check_secure(self):
        self.assertTrue(self.nsp.host_check(self.request, {'is_secure': True}),
                        self.nsp.witness.host_check.return_value)


class MockAutonomousPlugin(AutonomousMixin, _MockAAAPlugin):
    pass


class TestAutonmousMixin(unittest.TestCase):
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

    def test_authserver_pass(self):
        r = self.nsp.authserver_check({
            'login': 'global',
            'msg': 'msg',
            'signature': 'sign'
        })
        self.assertEqual(r, self.nsp.witness.authserver_check.return_value)

    def test_authserver_check_bad_sign(self):
        with mock.patch.object(self.nsp, 'sign', return_value='sign'):
            self.assertTrue(isinstance(self.nsp.authserver_check({
                'login': 'local_master',
                'msg': 'msg',
                'signature': 'bad'
            }), Fail))


class TestGetClass(unittest.TestCase):
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


class TestAAAPlugin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch_checker = mock.patch('napixd.plugins.auth.AAAChecker',
                                       spec=AAAChecker)

    def setUp(self):
        self.conf = Conf({'auth_url': u'http://napix.io/auth/authorization/'})
        self.headers = {
            'Authorization': 'method=GET&path=/&host=server.napix.nx:sign'
        }
        self.environ = {}
        self.request = mock.Mock(spec=Request,
                                 headers=self.headers,
                                 environ=self.environ,
                                 path='/',
                                 query_string='',
                                 method='GET')
        self.cb = mock.Mock()
        self.Checker = self.patch_checker.start()
        self.checker = self.Checker.return_value
        self.checker.authserver_check.return_value = Success()
        self.hosts = None

    def tearDown(self):
        self.patch_checker.stop()

    def plugin(self):
        return AAAPlugin(self.conf, 'server.napix.nx', hosts=self.hosts)

    def call(self):
        try:
            return self.plugin()(self.cb, self.request)
        except HTTPError as err:
            return err

    def test_call(self):
        r = self.call()
        self.assertEqual(r, self.cb.return_value)
        self.checker.authserver_check.assert_called_once_with({
            'msg': 'method=GET&path=/&host=server.napix.nx',
            'path': '/',
            'host': 'server.napix.nx',
            'method': 'GET',
            'signature': 'sign'
        })

    def test_refuse_request(self):
        self.request.path = '/abc/'
        r = self.call()
        self.assertEqual(r.status, 403)

    def test_refuse_path(self):
        self.request.method = 'POST'
        r = self.call()
        self.assertEqual(r.status, 403)

    def test_refuse_host(self):
        self.hosts = ['server.napix.io']
        r = self.call()
        self.assertEqual(r.status, 403)

    def test_authorize_host(self):
        self.hosts = ['server.napix.nx']
        r = self.call()
        self.assertEqual(r, self.cb.return_value)

    def test_refuse_host_list(self):
        self.hosts = ['server.napix.org', 'server.napix.io']
        r = self.call()
        self.assertEqual(r.status, 403)

    def test_no_authentication(self):
        del self.headers['Authorization']
        r = self.call()
        self.assertEqual(r.status, 401)

    def test_bad_authentication(self):
        self.headers['Authorization'] = 'garbagegarbage'
        r = self.call()
        self.assertEqual(r.status, 401)

    def test_refuse_list_method(self):
        self.request.method = 'POST'
        self.headers['Authorization'] = 'method=POST&path=/&host=server.napix.nx:sign'
        self.checker.authserver_check.return_value = Fail(['/abc/def', '/ghi/'])
        r = self.call()
        self.assertEqual(r.status, 403)

    def test_refuse_list(self):
        self.checker.authserver_check.return_value = Fail(['/abc/def', '/ghi/'])
        r = self.call()
        self.assertEqual(r.status, 203)
        self.assertEqual(r.body, ['/abc/def', '/ghi/'])

    def test_refuse_resource(self):
        self.request.path = '/abc/def'
        self.headers['Authorization'] = 'method=GET&path=/abc/def&host=server.napix.nx:sign'
        self.checker.authserver_check.return_value = Fail(['/abc/def', '/ghi/'])
        r = self.call()
        self.assertEqual(r.status, 403)

    def test_refuse_list_star(self):
        p = mock.MagicMock(name='permset')
        p.on_host.return_value = p
        p.filter_paths.return_value = ['/abc']
        c = self.checker.authserver_check.return_value = mock.MagicMock(
            spec=Fail,
            raw=['/ab*/', '/ghi/'],
            content=p
        )
        c.__nonzero__.return_value = False
        resp = self.cb.return_value = ['/abc/', '/def/']

        r = self.call()
        self.assertEqual(r, p.filter_paths.return_value)
        p.on_host.assert_called_once_with('server.napix.nx')
        p.filter_paths.assert_called_once_with(resp)

    def test_refuse_dict_star(self):
        p = mock.MagicMock(name='permset')
        p.on_host.return_value = p
        p.filter_paths.return_value = ['/abc']
        c = self.checker.authserver_check.return_value = mock.MagicMock(
            spec=Fail,
            raw=['/ab*/', '/ghi/'],
            content=p
        )
        c.__nonzero__.return_value = False
        resp = self.cb.return_value = {
            '/abc': {'this': 1},
            '/def': {'that': 2},
        }

        r = self.call()
        self.assertEqual(r, {'/abc': {'this': 1}})
        p.on_host.assert_called_once_with('server.napix.nx')
        p.filter_paths.assert_called_once_with(resp)
