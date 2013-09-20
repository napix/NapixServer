#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
import bottle
import mock
import json

from napix.exceptions import HTTPError

from napixd.plugins.exceptions import ExceptionsCatcher


class TestExceptionCatcher(unittest2.TestCase):

    @classmethod
    def setUpClass(self):
        self.requester = mock.patch('bottle.request', method='GET', path='/')

    def setUp(self):
        self.exc = exc = ExceptionsCatcher()
        self.requester.start()
        self.success = mock.MagicMock(__name__='callback')
        self.cb = exc.apply(self.success, mock.Mock())

    def tearDown(self):
        self.requester.stop()

    def test_success(self):
        self.success.return_value = 'abcdef'
        self.assertEqual(self.cb(), 'abcdef')

    def test_raise(self):
        self.success.side_effect = Exception()

        resp = self.cb()

        self.assertIsInstance(resp, bottle.HTTPResponse)
        self.assertEqual(resp.headers['Content-type'], 'application/json')
        body = json.loads(resp.body)
        self.assertDictEqual(body['request'], {
            'method': 'GET', 'path': '/', 'query': {}
        })

    def test_error(self):
        self.success.side_effect = previous_error = bottle.HTTPError(400, 'feels bad')
        resp = self.cb()

        self.assertIs(resp, previous_error)

    def test_filter(self):
        self.exc.napix_path = '/a/b'
        self.success.side_effect = Exception()

        with mock.patch('napixd.plugins.exceptions.traceback') as traceback:
            traceback.extract_tb.return_value = [
                ['/a/b/fname', 12, 'function', 'patoum(1, 2, 3)'],
                ['/c/d/fname', 12, 'function', 'patoum(1, 2, 3)'],
            ]
            resp = self.cb()

        body = json.loads(resp.body)
        self.assertEqual(body['traceback'], [
            {
                'filename': '/c/d/fname',
                'line': 12,
                'in': 'function',
                'call': 'patoum(1, 2, 3)',
            }
        ])

    def test_remote_exception(self):
        request = 'GET server.napix.nx/captains'
        response = mock.Mock()
        cause = {
            'traceback': [],
            'error_class': 'ValueError',
        }
        self.success.side_effect = HTTPError(request, cause, response)

        resp = self.cb()
        body = json.loads(resp.body)

        self.assertEqual(body['remote_call'], 'GET server.napix.nx/captains')
        self.assertEqual(body['remote_error'], {
            'traceback': [],
            'error_class': 'ValueError',
        })

    def test_remote_error(self):
        request = 'GET server.napix.nx/captains'
        response = mock.Mock()
        cause = '403 Forbidden'
        self.success.side_effect = remote_error = HTTPError(request, cause, response)

        resp = self.cb()
        body = json.loads(resp.body)

        self.assertEqual(body['remote_call'], 'GET server.napix.nx/captains')
        self.assertEqual(body['remote_error'], str(remote_error))

    def test_filter_intern(self):
        self.exc.napix_path = '/a/b'
        self.success.side_effect = Exception()

        with mock.patch('napixd.plugins.exceptions.traceback') as traceback:
            traceback.extract_tb.return_value = [
                ['/a/b/fname', 12, 'function', 'patoum(1, 2, 3)'],
                ['/a/b/fname', 12, 'function', 'patoum(1, 2, 3)'],
            ]
            resp = self.cb()

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
