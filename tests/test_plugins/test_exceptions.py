#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
import mock
import functools

from napix.exceptions import HTTPError

from napixd.plugins.exceptions import ExceptionsCatcher


class TestExceptionCatcher(unittest2.TestCase):
    def setUp(self):
        self.cb = mock.Mock()
        self.exc = ExceptionsCatcher(self.cb)
        self.environ = env = {
            'REQUEST_METHOD': 'GET',
            'REQUEST_URI': '/abc'
        }
        self.start_resp = sr = mock.Mock()
        self.application = functools.partial(self.exc, env, sr)

    def test_success(self):
        resp = self.application()

        self.cb.assert_called_once_with(self.environ, self.start_resp)
        self.assertEqual(resp, self.cb.return_value)

    def test_re_raise(self):
        self.cb.side_effect = KeyboardInterrupt()
        self.assertRaises(KeyboardInterrupt, self.application)

    def test_raise(self):
        self.cb.side_effect = Exception()

        with mock.patch.object(self.exc, 'extract_error', return_value={'a': 1}):
            resp = self.application()

        self.start_resp.assert_called_once_with('500 Internal Error', mock.ANY)
        status, headers = self.start_resp.call_args[0]

        headers = dict(headers)
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(''.join(resp), '{"a": 1}')

    def test_filter(self):
        self.exc.napix_path = '/a/b'

        with mock.patch('napixd.plugins.exceptions.traceback') as traceback:
            traceback.extract_tb.return_value = [
                ['/a/b/fname', 12, 'function', 'patoum(1, 2, 3)'],
                ['/c/d/fname', 12, 'function', 'patoum(1, 2, 3)'],
            ]
            body = self.exc.extract_error(self.environ, Exception())

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
        response = mock.Mock(status=500, reason='Internal Error')
        cause = {
            'traceback': [],
            'error_class': 'ValueError',
        }
        err = HTTPError(request, cause, response)

        with mock.patch('napixd.plugins.exceptions.traceback') as traceback:
            traceback.extract_tb.return_value = [
                ['/c/d/fname', 12, 'function', 'patoum(1, 2, 3)'],
            ]
            body = self.exc.extract_error(self.environ, err)

        self.assertEqual(body['remote_call'], 'GET server.napix.nx/captains')
        self.assertEqual(body['remote_error'], {
            'traceback': [],
            'error_class': 'ValueError',
        })

    def test_remote_error(self):
        request = 'GET server.napix.nx/captains'
        response = mock.Mock()
        cause = '403 Forbidden'
        remote_error = HTTPError(request, cause, response)

        with mock.patch('napixd.plugins.exceptions.traceback') as traceback:
            traceback.extract_tb.return_value = [
                ['/c/d/fname', 12, 'function', 'patoum(1, 2, 3)'],
            ]
            body = self.exc.extract_error(self.environ, remote_error)

        self.assertEqual(body['remote_call'], 'GET server.napix.nx/captains')
        self.assertEqual(body['remote_error'], str(remote_error))

    def test_filter_intern(self):
        self.exc.napix_path = '/a/b'

        with mock.patch('napixd.plugins.exceptions.traceback') as traceback:
            traceback.extract_tb.return_value = [
                ['/a/b/fname', 12, 'function', 'patoum(1, 2, 3)'],
                ['/a/b/fname', 12, 'function', 'patoum(1, 2, 3)'],
            ]
            body = self.exc.extract_error(self.environ, Exception())

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
