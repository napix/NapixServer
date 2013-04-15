#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
import bottle
import mock
import json

from napixd.plugins.exceptions import ExceptionsCatcher

class TestExceptionCatcher( unittest2.TestCase):
    @classmethod
    def setUpClass(self):
        self.requester = mock.patch( 'bottle.request', method='GET', path='/')

    def setUp(self):
        exc = ExceptionsCatcher()
        self.requester.start()
        self.cb = exc.apply( self.success, mock.Mock())

    def tearDown(self):
        self.requester.stop()

    def success(self, exc):
        raise exc

    def test_raise(self):
        resp = self.cb( Exception())
        self.assertIsInstance( resp, bottle.HTTPResponse)
        self.assertEqual( resp.headers['Content-type'], 'application/json')
        body = json.loads( resp.body)
        self.assertDictEqual( body['request'], {
            'method' : 'GET', 'path' : '/'
            })

    def test_error(self):
        previous_error = bottle.HTTPError( 400, 'feels bad')
        resp = self.cb( previous_error)
        self.assertIs( resp, previous_error)


