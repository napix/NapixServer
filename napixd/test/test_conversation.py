#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
from cStringIO import StringIO
from napixd.conf import Conf
from napixd.services import Service
from napixd.loader import NapixdBottle
from napixd.test.mock.managed_class import Paragraphs


class TestConversationPlugin(unittest2.TestCase):
    def setUp(self):
        self.bottle = NapixdBottle([ Service(Paragraphs,Conf({})) ])
        self.bottle.setup_bottle()

    def _make_env(self,method,url,body=None):
        body_ = StringIO()
        if body:
            body_.write(body)
            body_.seek(0)
        return {
                'wsgi.input' :body_,
                'wsgi.errors' : open('/dev/null','w'),
                'PATH_INFO': url,
                'HTTP_HOST': 'napix.test',
                'REQUEST_METHOD': method,
                'SERVER_PROTOCOL' : 'HTTP/1.1',
                'CONTENT_TYPE' : (body and 'application/json'
                    or 'application/x-www-form-urlencoded'),
                'CONTENT_LENGTH' : body and len(body) or 0
                }
    def _start_response(self, status_line, headers):
        self.status_line = status_line
        self.headers = headers

    def _do_request(self,env):
        resp = self.bottle.wsgi(env,self._start_response)
        code,_,status = self.status_line.partition(' ')
        return int(code), dict(self.headers), ''.join(resp)

    def testCreated(self):
        env = self._make_env('POST','/p/','{"text":"The bird flies in the sky"}')
        code, headers, result = self._do_request(env)
        self.assertEqual( code, 202)
        self.assertEqual( headers['Content-Length'], '0')
        self.assertEqual( headers['Location'], '/p/bird')
        self.assertEqual( result, '')

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
        self.assertEqual( result, '{"line": 40, "error_class": "ValueError",'
                ' "error_text": "I don\'t like cats", "filename": '
                '"/home/cecedille1/enix/napix6/lib/python2.6/s'
                'ite-packages/napixd/test/mock/managed_class.py"}')
        self.assertEqual( headers['Content-Type'], 'application/json')

    def testBadRequest(self):
        env = self._make_env('GET', '/p/lol')
        code, headers, result = self._do_request(env)
        self.assertEqual( code, 400)
        self.assertEqual( headers['Content-Type'], 'application/json')
        self.assertEqual( result, '"Story must be constructed about a pet"')

    def testBadJson(self):
        env = self._make_env('POST', '/p/', 'junk{"data')
        code, headers, result = self._do_request(env)
        self.assertEqual( code, 400)
        self.assertEqual( headers['Content-Type'], 'text/plain')
        self.assertEqual( result, 'Unable to load JSON object')

if __name__ == '__main__':
    unittest2.main()
