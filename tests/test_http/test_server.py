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
        self.cb = self.router.resolve.return_value

        with mock.patch('napixd.http.server.Router', return_value=r):
            self.server = WSGIServer()

    def test_wsgi_interface(self):
        environ = mock.MagicMock()
        start_resp = mock.Mock()

        with mock.patch('napixd.http.server.Request') as R:
            with mock.patch.object(self.server, 'handle') as handle:
                with mock.patch.object(self.server, 'cast') as Cast:
                    resp = self.server(environ, start_resp)

        handle.assert_called_once_with(R.return_value)
        Cast.assert_called_once_with(handle.return_value)
        cast = Cast.return_value
        start_resp.assert_called_once_with(cast.status_line, cast.headers.items())
        self.assertEqual(resp, cast.body)

    def test_wsgi_interface_http_error(self):
        environ = mock.MagicMock()
        start_resp = mock.Mock()
        error = HTTPError(418)

        with mock.patch('napixd.http.server.Request'):
            with mock.patch.object(self.server, 'handle', side_effect=error):
                with mock.patch.object(self.server, 'cast') as Cast:
                    resp = self.server(environ, start_resp)

        Cast.assert_called_once_with(error)
        cast = Cast.return_value
        self.assertEqual(resp, cast.body)

    def test_wsgi_interface_http_error_request(self):
        environ = mock.MagicMock()
        start_resp = mock.Mock()
        error = HTTPError(418)

        with mock.patch('napixd.http.server.Request', side_effect=error):
            with mock.patch.object(self.server, 'cast') as Cast:
                resp = self.server(environ, start_resp)

        Cast.assert_called_once_with(error)
        cast = Cast.return_value
        self.assertEqual(resp, cast.body)

    def test_handle_404(self):
        request = mock.Mock(spec=Request, path='/a/b')
        self.router.resolve.return_value = None
        resp = self.server.handle(request)
        self.assertEqual(resp.status, 404)

    def test_handle(self):
        request = mock.Mock(spec=Request, path='/a/b')
        resp = self.server.handle(request)
        self.cb.assert_called_once_with(request)
        self.assertEqual(resp, self.cb.return_value)

    def test_cast_text_plain(self):
        resp = self.server.cast(HTTPError(404, u'This does not exist'))
        self.assertEqual(resp.headers['Content-type'], 'text/plain; charset=utf-8')
        self.assertEqual(resp.body, ['This does not exist'])
        self.assertTrue(isinstance(resp.body[0], str))

    def test_cast_dict(self):
        resp = self.server.cast({'mpm': u'prefork'})
        self.assertEqual(resp.headers['content-type'], 'application/json')
        self.assertEqual(resp.headers['content-length'], 18)
        self.assertEqual(resp.body, ['{"mpm": "prefork"}'])
        self.assertTrue(isinstance(resp.body[0], str))

    def test_cast_response(self):
        r = HTTPResponse(302, {'Location': '/pim/pam/poum'}, u'See /pim/pam/poum')
        resp = self.server.cast(r)
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
        self.router1.resolve.return_value = None

        route = self.server.resolve('/a/b/c')
        self.router1.resolve.assert_called_once_with('/a/b/c')
        self.router2.resolve.assert_called_once_with('/a/b/c')
        self.assertEqual(route, self.router2.resolve.return_value)

    def test_no_priority(self):
        route = self.server.resolve('/a/b/c')
        self.router1.resolve.assert_called_once_with('/a/b/c')
        self.assertEqual(self.router2.resolve.call_count, 0)
        self.assertEqual(route, self.router1.resolve.return_value)

    def test_nothing(self):
        self.router1.resolve.return_value = None
        self.router2.resolve.return_value = None

        route = self.server.resolve('/a/b/c')
        self.assertEqual(route, None)
