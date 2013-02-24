#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
import bottle
import mock

from napixd.plugins import UserAgentDetector, ExceptionsCatcher

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
        self.assertIsInstance( resp, bottle.HTTPError)
        self.assertIsInstance( resp.body, dict)
        self.assertDictEqual( resp.body['request'], {
            'method' : 'GET', 'path' : '/'
            })

    def test_error(self):
        previous_error = bottle.HTTPError( 400, 'feels bad')
        resp = self.cb( previous_error)
        self.assertIs( resp, previous_error)


class TestHumanPlugin(unittest2.TestCase):
    def setUp(self):
        uad = UserAgentDetector()
        self.cb = uad.apply( self.success, mock.Mock())

    def success(self):
        return 'ok'

    def test_human_noauth(self):
        with mock.patch( 'bottle.request', headers={
            'user_agent' : 'Mozilla/5 blah blah'
            }):
            resp = self.cb()
        self.assertEqual( resp.status_code, 401)

    def test_human_debugauth(self):
        with mock.patch( 'bottle.request', GET={ 'authok': '' }, headers={
            'user_agent' : 'Mozilla/5 blah blah'
            }):
            resp = self.cb()
        self.assertEqual( resp, 'ok')

    def test_human_success_auth(self):
        with mock.patch( 'bottle.request', GET={ 'authok': '' }, headers={
            'user_agent' : 'Mozilla/5 blah blah',
            'Authorization' : 'host=napix.test:sign',
            }):
            resp = self.cb()
        self.assertEqual( resp, 'ok')

    def test_bot_failed_auth(self):
        with mock.patch( 'bottle.request', GET={ 'authok': '' }, headers={
            'user_agent' : 'Mozilla/5 blah blah',
            'Authorization' : 'host=napix.test:sign',
            }):
            resp = self.cb()
        self.assertEqual( resp, 'ok')

if __name__ == '__main__':
    unittest2.main()
