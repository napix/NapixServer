#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
import json

from napixd.conf import Conf
from napixd.services import Service
from napixd.loader import NapixdBottle
from napixd.plugins import UserAgentDetector

from mock.managed_class import Paragraphs
from bases import WSGITester

class TestConversationPlugin(WSGITester):
    def setUp(self):
        self.bottle = NapixdBottle([ Service(Paragraphs,Conf({})) ])
        self.bottle.setup_bottle()
    def testCreated(self):
        env = self._make_env('POST','/p/','{"text":"The bird flies in the sky"}')
        code, headers, result = self._do_request(env)
        self.assertEqual( code, 201)
        self.assertEqual( headers['Content-Length'], '0')
        self.assertEqual( headers['Location'], '/p/bird')
        self.assertEqual( result, '')

    def testURLEncoded(self):
        env = self._make_env('POST','/p/',r'text=The%20bird%20flies%20in%20the%20sky', url_encoded=True)
        code, headers, result = self._do_request(env)
        self.assertEqual( code, 201)

    def testSerializeList(self):
        env = self._make_env('GET', '/p/cat/')
        code, headers, result = self._do_request(env)
        self.assertEqual( code, 200)
        self.assertEqual( headers['Content-Type'], 'application/json')
        self.assertEqual( result, '["/p/cat/the", "/p/cat/eats", "/p/cat/cat"]')

    def testSerializeDict(self):
        env = self._make_env('GET', '/p/cat')
        code, headers, result = self._do_request(env)
        self.assertEqual( code, 200)
        self.assertEqual( headers['Content-Type'], 'application/json')
        self.assertEqual( result, '{"text": "the cat eats"}')

    def testError(self):
        env = self._make_env('GET', '/p/cat/cat/t/french')
        code, headers, result = self._do_request(env)
        self.assertEqual( code, 500)
        self.assertEqual( headers['Content-Type'], 'application/json')
        res = json.loads(result)
        self.assertEqual( res['line'], 41)
        self.assertEqual( res['error_class'], 'ValueError')
        self.assertEqual( res['error_text'], "I don't like cats")
        self.assertTrue( isinstance( res['traceback'], list))

    def testBadRequest(self):
        env = self._make_env('GET', '/p/lol')
        code, headers, result = self._do_request(env)
        self.assertEqual( code, 400)
        self.assertEqual( headers['Content-Type'], 'text/plain')
        self.assertEqual( result, 'Story must be constructed about a pet')

    def testBadJson(self):
        env = self._make_env('POST', '/p/', 'junk{"data')
        code, headers, result = self._do_request(env)
        self.assertEqual( code, 400)
        self.assertEqual( headers['Content-Type'], 'text/plain')
        self.assertEqual( result, 'Unable to load JSON object')

    def testResponse(self):
        env = self._make_env('GET', '/p/cat/cat/l/a',query='format=xml')
        code, headers, result = self._do_request(env)
        self.assertEqual( code, 200)
        self.assertEqual( headers['Content-Type'], 'application/xml')
        self.assertEqual( result, '<letter ord="97">a</letter>')

    def testResponseEmpty(self):
        env = self._make_env('GET', '/p/cat/cat/l/a',query='format=empty')
        code, headers, result = self._do_request(env)
        self.assertEqual( code, 200)
        self.assertEqual( headers.get('My-Own-Header'), 'napix')

class TestHumanPlugin(WSGITester):
    def setUp(self):
        self.bottle = NapixdBottle([ Service(Paragraphs,Conf({})) ])
        self.bottle.install( UserAgentDetector())
        self.bottle.setup_bottle()

    def test_human_noauth(self):
        env = self._make_env('GET', '/p/', auth=False, agent='Mozilla/5 blah blah')
        code, headers, result = self._do_request(env)
        self.assertEqual( headers['Content-Type'], 'text/html')

    def test_human_debugauth(self):
        env = self._make_env('GET', '/p/', auth=False, query='authok', agent='Mozilla/5 blah blah')
        code, headers, result = self._do_request(env)
        self.assertEqual( headers['Content-Type'], 'application/json')

    def test_human_success_auth(self):
        env = self._make_env('GET', '/p/', auth='host=napix.test:sign',agent='Mozilla/5 blah blah' )
        code, headers, result = self._do_request(env)
        self.assertEqual( headers['Content-Type'], 'application/json')

    def test_bot_failed_auth(self):
        env = self._make_env('GET', '/p/', auth=False, agent='Curl blah blah')
        code, headers, result = self._do_request(env)
        self.assertEqual( headers['Content-Type'], 'application/json')

if __name__ == '__main__':
    unittest2.main()
