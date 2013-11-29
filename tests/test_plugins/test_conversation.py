#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

import functools

from napixd.plugins.conversation import UserAgentDetector


class TestHumanPlugin(unittest.TestCase):

    def setUp(self):
        uad = UserAgentDetector()
        self.headers = {}
        self.request = mock.Mock(headers=self.headers)
        self.cb = functools.partial(uad, mock.Mock(return_value='ok'), self.request)

    def success(self):
        return 'ok'

    def test_human_ajax(self):
        self.headers['user_agent'] = 'Mozilla/5 blah blah'
        self.headers['X-Requested-With'] = 'XMLHttpRequest'
        resp = self.cb()
        self.assertEqual(resp, 'ok')

    def test_human_noauth(self):
        self.headers['user_agent'] = 'Mozilla/5 blah blah'
        resp = self.cb()
        self.assertEqual(resp.status, 401)

    def test_human_success_auth(self):
        self.headers['user_agent'] = 'Mozilla/5 blah blah'
        self.headers['Authorization'] = 'host=napix.test:sign'
        resp = self.cb()
        self.assertEqual(resp, 'ok')

    def test_bot_failed_auth(self):
        self.headers['user_agent'] = 'curl blah blah'
        resp = self.cb()
        self.assertEqual(resp, 'ok')
