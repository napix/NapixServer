#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

from napixd.plugins.times import (
    WaitPlugin,
    TimePlugin,
)


class TestWaitPlugin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.Chrono_patch = mock.patch('napixd.plugins.times.Chrono')

    def setUp(self):
        self.wp = WaitPlugin(5000)
        self.cb = mock.Mock()
        self.r = mock.Mock()
        self.C = self.Chrono_patch.start()
        self.c = self.C.return_value.__enter__.return_value = self.C.return_value

    def tearDown(self):
        self.C.stop()

    def call(self):
        return self.wp(self.cb, self.r)

    def test_no_wait(self):
        self.c.total = 10
        with mock.patch('napixd.plugins.times.time') as time:
            r = self.call()

        self.assertEqual(time.sleep.call_count, 0)
        self.assertEqual(r, self.cb.return_value)

    def test_wait(self):
        self.c.total = 4
        with mock.patch('napixd.plugins.times.time') as time:
            r = self.call()

        time.sleep.assert_called_once_with(1)
        self.assertEqual(r, self.cb.return_value)
