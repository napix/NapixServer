#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

from cStringIO import StringIO

from napixd.http.request import Request, InputStream, Query
from napixd.http.response import HTTPError


class TestQuery(unittest.TestCase):
    def test_query_string_none(self):
        s = Query('a')
        self.assertEqual(s['a'], None)

    def test_contains(self):
        self.assertTrue('a' in Query('a'))
        self.assertTrue('a' in Query('a='))
        self.assertTrue('a' in Query('a=b'))

    def test_query_string_nothing(self):
        s = Query('a=1')
        self.assertRaises(KeyError, lambda: s['b'])

    def test_query_label_escaped_contains(self):
        s = Query('a%2fb&a%40b')
        self.assertTrue('a/b' in s)
        self.assertTrue('a@b' in s)

    def test_query_label_escaped(self):
        s = Query('a%2fb=1')
        self.assertEqual(s['a/b'], '1')

    def test_query_value_escaped(self):
        s = Query('a=1%2f0')
        self.assertEqual(s['a'], '1/0')

    def test_query_values_escaped(self):
        s = Query('a=1%2f0&a=2%2f3')
        self.assertEqual(s.getall('a'), ['1/0', '2/3'])

    def test_query_string_value(self):
        s = Query('a=1')
        self.assertEqual(s['a'], '1')

    def test_query_string_empty(self):
        s = Query('a=')
        self.assertEqual(s['a'], '')

    def test_query_string_values(self):
        s = Query('a=1&a=2')
        self.assertEqual(s['a'], '1')

    def test_query_all_values(self):
        s = Query('a=1&a=2')
        self.assertEqual(s.getall('a'), ['1', '2'])

    def test_query_all_one(self):
        s = Query('a=1')
        self.assertEqual(s.getall('a'), ['1'])

    def test_query_all_none(self):
        s = Query('a=1')
        self.assertEqual(s.getall('c'), [])

    def test_dict(self):
        s = Query({'a': 'abc'})
        self.assertEqual(s.getall('a'), ['abc'])

    def test_copy(self):
        s = Query({'a': 'abc'})
        s = Query(s)
        self.assertEqual(s.getall('a'), ['abc'])


class TestRequest(unittest.TestCase):
    def _r(self, **values):
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '',
        }
        environ.update(values)
        return Request(environ)

    def test_path(self):
        r = self._r()
        self.assertEqual(r.path, '/')
        self.assertEqual(r.method, 'GET')

    def test_content_type(self):
        r = self._r(CONTENT_TYPE='text/plain')
        self.assertEqual(r.content_type, 'text/plain')

    def test_content_length_negative(self):
        r = self._r(CONTENT_LENGTH='-1234')
        self.assertEqual(r.content_length, 0)

    def test_content_length(self):
        r = self._r(CONTENT_LENGTH='1234')
        self.assertEqual(r.content_length, 1234)

    def test_no_content_length(self):
        r = self._r()
        self.assertEqual(r.content_length, 0)

    def test_bad_content_length(self):
        r = self._r(CONTENT_LENGTH='pim')
        self.assertEqual(r.content_length, 0)

    def test_query_string(self):
        r = self._r(QUERY_STRING='abc&def=ghi')
        self.assertEqual(r.query_string, 'abc&def=ghi')

    def test_query(self):
        r = self._r(QUERY_STRING='abc&def=ghi')
        self.assertEqual(r.query, {'abc': None, 'def': 'ghi'})

    def test_headers(self):
        r = self._r(HTTP_AUTHORIZATION='login:pass', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.headers, {
            'authorization': 'login:pass',
            'x-requested-with': 'XMLHttpRequest'
        })

    def test_body(self):
        input = mock.Mock()
        r = self._r(CONTENT_LENGTH=14, **{
            'wsgi.input': input
        })
        with mock.patch('napixd.http.request.InputStream') as IS:
            body = r._body()

        self.assertEqual(body, IS.return_value)
        IS.assert_called_once_with(input, 14)

    def test_body_cl_0(self):
        r = self._r(**{
            'wsgi.input': input
        })

        self.assertEqual(r._body().read(), '')

    def test_body_too_big(self):
        r = self._r(CONTENT_LENGTH=1e9, **{
            'wsgi.input': input
        })

        self.assertRaises(HTTPError, r._body)

    def test_request_json(self):
        data = '{ "mpm": "prefork", "x": 1 }'
        r = self._r(
            CONTENT_TYPE='application/json',
            CONTENT_LENGTH=len(data),
            **{
                'wsgi.input': StringIO(data)
            })

        self.assertEqual(r.data, {'mpm': 'prefork', 'x': 1})

    def test_request_bad_json(self):
        data = '{ "mpm": prefork", "x": 1 }'
        r = self._r(
            CONTENT_TYPE='application/json',
            CONTENT_LENGTH=len(data),
            **{
                'wsgi.input': StringIO(data)
            })

        self.assertRaises(HTTPError, lambda: r.data)

    def test_request_no_json(self):
        r = self._r(**{
            'wsgi.input': StringIO('')
        })

        self.assertEqual(r.data, {})

    def test_request_data_json(self):
        data = '<value><mpm>prefork</mpm><x>1</x></value>'
        r = self._r(
            CONTENT_TYPE='text/xml',
            CONTENT_LENGTH=len(data),
            **{
                'wsgi.input': StringIO(data)
            })

        self.assertRaises(HTTPError, lambda: r.data)


class TestInputStream(unittest.TestCase):
    def setUp(self):
        self.input = StringIO('01234567890')

    def test_read_all(self):
        ist = InputStream(self.input, 11)
        self.assertEqual(ist.read(), '01234567890')

    def test_read_eof(self):
        ist = InputStream(self.input, 11)
        self.assertEqual(ist.read(), '01234567890')
        self.assertEqual(ist.read(), '')

    def test_read_size_eof(self):
        ist = InputStream(self.input, 11)
        self.assertEqual(ist.read(11), '01234567890')
        self.assertEqual(ist.read(11), '')

    def test_read_all_after_eof(self):
        ist = InputStream(self.input, 10)
        self.assertEqual(ist.read(), '0123456789')
        self.assertEqual(ist.read(), '')

    def test_read_size_after_eof(self):
        ist = InputStream(self.input, 10)
        self.assertEqual(ist.read(11), '0123456789')
        self.assertEqual(ist.read(11), '')

    def test_read_all_before(self):
        ist = InputStream(self.input, 10)
        self.assertEqual(ist.read(), '0123456789')

    def test_read_size_after(self):
        ist = InputStream(self.input, 10)
        self.assertEqual(ist.read(5), '01234')
        self.assertEqual(ist.read(4), '5678')
        self.assertEqual(ist.read(3), '9')

    def test_read_size_all(self):
        ist = InputStream(self.input, 11)
        self.assertEqual(ist.read(5), '01234')
        self.assertEqual(ist.read(4), '5678')
        self.assertEqual(ist.read(3), '90')
