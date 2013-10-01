#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import

import unittest
import mock

from napixd.plugins.ratelimit import RateLimitingPlugin
from napixd.conf import Conf


class TestRateLimit(unittest.TestCase):
    def setUp(self):
        self.success = mock.MagicMock(__name__='callback')
        self.rl = RateLimitingPlugin(Conf())
        self.cb = self.rl.apply(self.success, mock.Mock())
