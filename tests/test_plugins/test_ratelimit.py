#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import

import unittest
import mock

from napixd.plugins.ratelimit import RateLimitingPlugin


class TestRateLimit(unittest.TestCase):
    def setUp(self):
        #2 requests max by 60 seconds
        self.con = mock.MagicMock()
        self.pipe = self.con.pipeline.return_value.__enter__.return_value = mock.Mock()
        self.rl = RateLimitingPlugin(2, 60, self.con)

    def call(self):
        self.cb = mock.Mock(name='callback')
        self.req = mock.Mock(
            name='request',
            environ={
                'REMOTE_ADDR': '191.144.12.13',
            }
        )
        with mock.patch('napixd.plugins.ratelimit.time') as time:
            time.time.return_value = 1200
            return self.rl(self.cb, self.req)

    def test_first_req(self):
        self.pipe.execute.return_value = [0, True, 0]
        resp = self.call()
        self.pipe.assert_has_calls([
            mock.call.zcount('rate_limit:191.144.12.13', 1140, 1200),
            mock.call.zadd('rate_limit:191.144.12.13', 1200, 1200),
            mock.call.expireat('rate_limit:191.144.12.13', 1260),
        ])
        self.assertEqual(resp, self.cb.return_value)

    def test_second_request(self):
        self.pipe.execute.return_value = [1, True, 0]
        resp = self.call()
        self.assertEqual(resp, self.cb.return_value)

    def test_third_request(self):
        self.pipe.execute.return_value = [2, True, 0]
        resp = self.call()
        self.assertEqual(resp.status, 429)
