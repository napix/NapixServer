#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock
import json

import base64

from napixd.auth.jwt import JSONWebToken
from napixd.http.response import HTTPError


class TestJSONWebToken(unittest.TestCase):
    def setUp(self):
        self.jwt = JSONWebToken()
        self.header = {
            'alg': 'HS256',
            'typ': 'JWT',
        }
        self.body = {
            'iss': 'login',
            'sub': 'GET /path/',
            'aud': 'server.napix.nx',
            'exp': 1234567,
            'jti': 'unique-unique',
        }

    def signed_body(self):
        header = self._b64json(self.header)
        body = self._b64json(self.body)
        return header + '.' + body

    def whole_jwt(self):
        return self.signed_body() + '.signature'

    def _b64json(self, body):
        return base64.urlsafe_b64encode(json.dumps(body))

    def call(self, jwt):
        return self.jwt.decode_jwt(jwt)

    def test_jwt(self):
        signed_body = self.signed_body()
        self.assertEqual(self.call(signed_body + '.signature'), {
            'host': u'server.napix.nx',
            'login': u'login',
            'method': u'GET',
            'msg': signed_body,
            'nonce': u'unique-unique',
            'path': u'/path/',
            'signature': 'signature',
            'is_secure': True,
            'timestamp': 1234567,
        })

    def test_bad_base64(self):
        self.assertEqual(self.call('pim.pam.poum=zib-zob'), None)

    def test_bad_json(self):
        self.assertEqual(self.call('pamFzb24=.pamFzb24=.signature'), None)

    def test_jwt_extra_header(self):
        self.header['cty'] = 'JWT'
        self.assertRaises(HTTPError, self.call, self.signed_body() + '.signature')

    def test_missing_key(self):
        del self.body['exp']
        self.assertRaises(HTTPError, self.call, self.signed_body() + '.signature')

    def test_bad_sub(self):
        self.body['sub'] = 'pim-pam-poum'
        self.assertRaises(HTTPError, self.call, self.signed_body() + '.signature')

    def test_http_detect(self):
        request = mock.Mock(headers={
            'Authorization': self.whole_jwt()
        })
        self.assertTrue(isinstance(self.jwt(request), dict))

    def test_http_no_detect(self):
        request = mock.Mock(headers={
            'Authorization': 'custom&auth=protocol'
        })
        self.assertTrue(self.jwt(request) is None)

    def test_http_no_detect_no_header(self):
        request = mock.Mock(headers={
        })
        self.assertTrue(self.jwt(request) is None)
