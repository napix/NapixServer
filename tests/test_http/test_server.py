#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

from napixd.http.server import WSGIServer
from napixd.http.router.router import Router
from napixd.http.response import HTTPError, HTTPResponse
from napixd.http.request import Request


class TestServer(unittest.TestCase):
    def setUp(self):
        self.router = r = mock.Mock(spec=Router)
        self.request = mock.Mock(spec=Request,
                                 path='/a/b',
                                 method='GET')
        self.cb = self.router.resolve.return_value

        with mock.patch('napixd.http.server.Router', return_value=r):
            self.server = WSGIServer()

        self.environ = mock.MagicMock()
        self.start_resp = mock.Mock()

    def call(self):
        with mock.patch('napixd.http.server.Request', return_value=self.request):
            return self.server(self.environ, self.start_resp)

    def cast(self, value):
        return self.server.cast(self.request, value)

    def test_wsgi_interface(self):
        with mock.patch.object(self.server, 'handle') as handle:
            with mock.patch.object(self.server, 'cast') as Cast:
                resp = self.call()

        handle.assert_called_once_with(self.request)
        Cast.assert_called_once_with(self.request, handle.return_value)
        cast = Cast.return_value
        self.start_resp.assert_called_once_with(cast.status_line, cast.headers.items())
        self.assertEqual(resp, cast.body)

    def test_wsgi_interface_http_error(self):
        self.router.resolve.side_effect = error = HTTPError(418)

        with mock.patch.object(self.server, 'cast') as Cast:
            resp = self.call()

        Cast.assert_called_once_with(self.request, error)
        cast = Cast.return_value
        self.assertEqual(resp, cast.body)

    def test_handle_404(self):
        self.router.resolve.return_value = None
        resp = self.server.handle(self.request)
        self.assertEqual(resp.status, 404)

    def test_handle(self):
        resp = self.server.handle(self.request)
        self.cb.assert_called_once_with(self.request)
        self.assertEqual(resp, self.cb.return_value)

    def test_cast_HEAD(self):
        self.request.method = 'HEAD'
        resp = self.cast('VALUE')
        self.assertEqual(resp.headers['Content-Length'], '0')
        self.assertEqual(resp.body, [])

    def test_cast_text_plain(self):
        resp = self.server.cast(HTTPError(404, u'This does not exist'))
        self.assertEqual(resp.headers['Content-type'], 'text/plain; charset=utf-8')
        self.assertEqual(resp.body, ['This does not exist'])
        self.assertTrue(isinstance(resp.body[0], str))

    def test_cast_dict(self):
        resp = self.cast({'mpm': u'prefork'})
        self.assertEqual(resp.headers['content-type'], 'application/json')
        self.assertEqual(resp.headers['content-length'], 18)
        self.assertEqual(resp.body, ['{"mpm": "prefork"}'])
        self.assertTrue(isinstance(resp.body[0], str))

    def test_cast_response(self):
        r = HTTPResponse(302, {'Location': '/pim/pam/poum'}, u'See /pim/pam/poum')
        resp = self.cast(r)
        self.assertEqual(resp.status, 302)
        self.assertEqual(resp.headers['Location'], '/pim/pam/poum')
        self.assertEqual(resp.headers['content-type'], 'text/plain; charset=utf-8')
        self.assertEqual(resp.headers['content-length'], 17)
        self.assertEqual(resp.body, ['See /pim/pam/poum'])


class TestServerRouter(unittest.TestCase):
    def setUp(self):
        self.router1 = r1 = mock.Mock(spec=Router)
        self.router2 = r2 = mock.Mock(spec=Router)

        with mock.patch('napixd.http.server.Router', return_value=r1):
            self.server = WSGIServer()
        with mock.patch('napixd.http.server.Router', return_value=r2):
            self.server.push()

    def test_router(self):
        self.assertEqual(self.server.router, self.router1)

    def test_priority(self):
        self.router2.resolve.return_value = None

        route = self.server.resolve('/a/b/c')
        self.router1.resolve.assert_called_once_with('/a/b/c')
        self.router2.resolve.assert_called_once_with('/a/b/c')
        self.assertEqual(route, self.router1.resolve.return_value)

    def test_no_priority(self):
        route = self.server.resolve('/a/b/c')
        self.router2.resolve.assert_called_once_with('/a/b/c')
        self.assertEqual(self.router1.resolve.call_count, 0)
        self.assertEqual(route, self.router2.resolve.return_value)

    def test_nothing(self):
        self.router1.resolve.return_value = None
        self.router2.resolve.return_value = None

        route = self.server.resolve('/a/b/c')
        self.assertEqual(route, None)
