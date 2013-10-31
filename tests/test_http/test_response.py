#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

from napixd.http.response import HTTPResponse
from napixd.http.headers import HeadersDict


class TestResponse(unittest.TestCase):

    def test_0_args(self):
        r = HTTPResponse()

        self.assertEqual(r.status, 200)
        self.assertEqual(len(r.headers), 0)
        self.assertTrue(isinstance(r.headers, HeadersDict))
        self.assertEqual(r.body, None)

    def test_1_arg(self):
        body = mock.Mock()
        r = HTTPResponse(body)

        self.assertEqual(r.status, 200)
        self.assertEqual(len(r.headers), 0)
        self.assertTrue(isinstance(r.headers, HeadersDict))
        self.assertEqual(r.body, body)

    def test_2_args(self):
        body = mock.Mock()
        r = HTTPResponse({'content_type': 'application/pdf'}, body)

        self.assertEqual(r.status, 200)
        self.assertEqual(r.headers['content-type'], 'application/pdf')
        self.assertTrue(isinstance(r.headers, HeadersDict))
        self.assertEqual(r.body, body)

    def test_3_args(self):
        body = mock.Mock()
        r = HTTPResponse(304, {'content_type': 'application/pdf'}, body)

        self.assertEqual(r.status, 304)
        self.assertEqual(r.headers['content-type'], 'application/pdf')
        self.assertEqual(r.body, body)

    def test_4_args(self):
        self.assertRaises(TypeError, HTTPResponse, 200, {}, 'body', 'more')

    def test_status_line(self):
        r = HTTPResponse(204, {}, None)
        self.assertEqual(r.status_line, '204 No Content')

    def test_status_line_unknown(self):
        r = HTTPResponse(198, {}, None)
        self.assertEqual(r.status_line, '198 Unknown')


class TestResponseWithResponse(unittest.TestCase):
    def setUp(self):
        self.body = body = mock.Mock()
        self.r = HTTPResponse(201, {'header1': 'value1'}, body)

    def test_keep_status(self):
        r = HTTPResponse(self.r)
        self.assertEqual(r.status, 201)

    def test_override_status(self):
        r = HTTPResponse(200, {}, self.r)
        self.assertEqual(r.status, 200)

    def test_keep_body(self):
        r = HTTPResponse(self.r)
        self.assertEqual(r.body, self.body)

    def test_merge_headers(self):
        r = HTTPResponse({'header2': 'value2'}, self.r)

        self.assertEqual(r.headers['header1'], 'value1')
        self.assertEqual(r.headers['header2'], 'value2')

    def test_override_header(self):
        r = HTTPResponse({'header1': 'value2'}, self.r)

        self.assertEqual(r.headers['header1'], 'value2')
