#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import

import unittest
import mock

from napixd.http.response import HTTPError, HTTPResponse
from napixd.plugins.ratelimit import RateLimiterPlugin


class TestRateLimiterPlugin(unittest.TestCase):
    def setUp(self):
        #2 requests max by 60 seconds
        self.con = mock.MagicMock()
        self.pipe = self.con.pipeline.return_value.__enter__.return_value = mock.Mock()
        self.criteria = c = mock.Mock(return_value='123')
        self.rl = RateLimiterPlugin(2, 60, self.con, c)

    def call(self):
        self.cb = mock.Mock(name='callback')
        self.req = mock.Mock(name='request')
        with mock.patch('napixd.plugins.ratelimit.time') as time:
            time.time.return_value = 1200
            return self.rl(self.cb, self.req)

    def test_first_req(self):
        self.pipe.zcount.return_value = 0
        resp = self.call()
        self.pipe.assert_has_calls([
            mock.call.watch('rate_limit:123'),
            mock.call.zcount('rate_limit:123', 1140, 1200),
            mock.call.multi(),
            mock.call.zadd('rate_limit:123', 1200, 1200),
            mock.call.expireat('rate_limit:123', 1260),
        ])
        self.assertEqual(resp, HTTPResponse({
            'x-ratelimit-remaining': '2',
            'x-ratelimit-limit': '2/60s',
            'x-ratelimit-used': '0',
        }, self.cb.return_value))

    def test_second_request(self):
        self.pipe.zcount.return_value = 1
        resp = self.call()
        self.assertEqual(resp, HTTPResponse({
            'x-ratelimit-remaining': '1',
            'x-ratelimit-limit': '2/60s',
            'x-ratelimit-used': '1',
        }, self.cb.return_value))
        self.criteria.assert_called_once_with(self.req)

    def test_third_request(self):
        self.pipe.zcount.return_value = 2
        resp = self.call()
        self.assertEqual(resp.status, 429)
        self.pipe.assert_has_calls([
            mock.call.watch('rate_limit:123'),
            mock.call.zcount('rate_limit:123', 1140, 1200),
            mock.call.execute(),
        ])
