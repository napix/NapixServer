#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
import bottle
import mock
import json

from napixd.plugins.conversation import ConversationPlugin, UserAgentDetector


class TestConversationUnwrap( unittest2.TestCase):
    def setUp(self):
        self.cp = ConversationPlugin()

    def make_request(self, headers, body):
        body = mock.Mock(**{
            'read.return_value' : body
            })
        request = mock.MagicMock( body=body)
        request.get = headers.get
        request.__getitem__ = lambda self,key: headers[key]
        request.__contains__ = lambda self,key: key in headers
        return request

    def test_unwrap_bad_json(self):
        request = self.make_request({
                'CONTENT_LENGTH' : '100',
                'CONTENT_TYPE' : 'application/json',
                }, '{"ab": "candlej')
        with self.assertRaises( bottle.HTTPError) as resp:
            self.cp.unwrap( request)
        self.assertEqual( resp.exception.status_code, 400)

    def test_unwrap_json(self):
        obj = { 'ab' : 12 }
        request = self.make_request({
                'CONTENT_LENGTH' : '100',
                'CONTENT_TYPE' : 'application/json',
                }, json.dumps( obj))
        self.cp.unwrap( request)
        self.assertEqual( request.data, { 'ab': 12 })

    def test_unwrap_empty(self):
        request = self.make_request({
                'CONTENT_LENGTH' : '0',
                }, '')
        self.cp.unwrap( request)
        self.assertEqual( request.data, {})

    def test_unwrap_urlencoded(self):
        request = self.make_request({
                'CONTENT_LENGTH' : '100',
                'CONTENT_TYPE' : 'application/x-www-form-urlencoded',
                }, '')
        request.forms = { 'ab': 12 }
        self.cp.unwrap( request)
        self.assertEqual( request.data, { 'ab': 12 })


class TestConversationWrap( unittest2.TestCase):
    def setUp(self):
        cp = ConversationPlugin()
        cp.unwrap = mock.Mock({ 'ab' : 12 })
        self.cb = cp.apply( self.success, mock.Mock())

    def success(self, obj=None, exc=None):
        if exc is not None:
            raise exc
        return obj

    def test_request_head_404(self):
        with mock.patch('bottle.request', method='HEAD'):
            resp = self.cb(bottle.HTTPError(404, body='pouet' ))
        self.assertIsInstance(resp,  bottle.HTTPResponse)
        self.assertEqual( resp.status_code, 404)
        self.assertEqual( resp.headers['Content-Type'], '')
        self.assertEqual( resp.body, None)

    def test_request_head(self):
        with mock.patch('bottle.request', method='HEAD'):
            resp = self.cb({ 'a': 'b' })
        self.assertIsInstance(resp,  bottle.HTTPResponse )
        self.assertEqual( resp.status_code, 200)
        self.assertEqual( resp.headers['Content-Type'], '')
        self.assertEqual( resp.body, None)

    def test_conversation_object(self):
        resp = self.cb({ 'a': 'b' })
        self.assertIsInstance(resp,  bottle.HTTPResponse )
        self.assertEqual( resp.status_code, 200)
        self.assertEqual( resp.headers['Content-Type'], 'application/json')
        self.assertDictEqual( json.loads( resp.body), { 'a': 'b'})

    def test_conversation_nothing(self):
        resp = self.cb()
        self.assertIsInstance(resp,  bottle.HTTPResponse )
        self.assertEqual( resp.status_code, 200)
        self.assertEqual( resp.body, None)

    def test_returned_exception(self):
        resp = self.cb( bottle.HTTPResponse( 'I\'m a teapot', 418, x_excitant='theine'))
        self.assertEqual( resp.status_code, 418)
        self.assertEqual( resp.body, 'I\'m a teapot')
        self.assertEqual( resp.headers['x-excitant'], 'theine')
        self.assertEqual( resp.headers['content-type'], 'text/plain')

    def test_exception(self):
        resp = self.cb( None, bottle.HTTPResponse( 'I\'m a teapot', 418, x_excitant='theine'))
        self.assertEqual( resp.status_code, 418)
        self.assertEqual( resp.body, 'I\'m a teapot')
        self.assertEqual( resp.headers['x-excitant'], 'theine')
        self.assertEqual( resp.headers['content-type'], 'text/plain')

    def test_exception_custom_content_type(self):
        resp = self.cb( None, bottle.HTTPResponse( 'I\'m a teapot',
            content_type='application/caffe+sugar'))
        self.assertEqual( resp.headers['content-type'], 'application/caffe+sugar')

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

