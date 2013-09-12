#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
import bottle
import mock
import json

from napixd.plugins.exceptions import ExceptionsCatcher


class TestExceptionCatcher(unittest2.TestCase):

    @classmethod
    def setUpClass(self):
        self.requester = mock.patch('bottle.request', method='GET', path='/')

    def setUp(self):
        self.exc = exc = ExceptionsCatcher()
        self.requester.start()
        self.cb = exc.apply(self.success, mock.Mock())

    def tearDown(self):
        self.requester.stop()

    def success(self, exc):
        raise exc

    def test_raise(self):
        resp = self.cb(Exception())
        self.assertIsInstance(resp, bottle.HTTPResponse)
        self.assertEqual(resp.headers['Content-type'], 'application/json')
        body = json.loads(resp.body)
        self.assertDictEqual(body['request'], {
            'method': 'GET', 'path': '/'
        })

    def test_error(self):
        previous_error = bottle.HTTPError(400, 'feels bad')
        resp = self.cb(previous_error)
        self.assertIs(resp, previous_error)

    def test_filter(self):
        self.exc.napix_path = '/a/b'
        with mock.patch('napixd.plugins.exceptions.traceback') as traceback:
            traceback.extract_tb.return_value = [
                ['/a/b/fname', 12, 'function', 'patoum(1, 2, 3)'],
                ['/c/d/fname', 12, 'function', 'patoum(1, 2, 3)'],
            ]
            resp = self.cb(Exception())

        body = json.loads(resp.body)
        self.assertEqual(body['traceback'], [
            {
                'filename': '/c/d/fname',
                'line': 12,
                'in': 'function',
                'call': 'patoum(1, 2, 3)',
            }
        ])

    def test_filter_intern(self):
        self.exc.napix_path = '/a/b'
        with mock.patch('napixd.plugins.exceptions.traceback') as traceback:
            traceback.extract_tb.return_value = [
                ['/a/b/fname', 12, 'function', 'patoum(1, 2, 3)'],
                ['/a/b/fname', 12, 'function', 'patoum(1, 2, 3)'],
            ]
            resp = self.cb(Exception())

        body = json.loads(resp.body)
        self.assertEqual(body['traceback'], [
            {
                'filename': '/a/b/fname',
                'line': 12,
                'in': 'function',
                'call': 'patoum(1, 2, 3)',
            },
            {
                'filename': '/a/b/fname',
                'line': 12,
                'in': 'function',
                'call': 'patoum(1, 2, 3)',
            }
        ])
