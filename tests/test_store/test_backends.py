#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import unittest

from napixd.store.backends import BaseCounter


class MyCounter(BaseCounter):
    def __init__(self, name):
        super(MyCounter, self).__init__()
        self.value = 0

    def increment(self, by=1):
        self.value += by
        return self.value

    def reset(self, to=1):
        self.value = to


class TestBaseCounter(unittest.TestCase):
    def setUp(self):
        self.be = MyCounter('name')
        self.inc = self.be.increment = mock.Mock(side_effect=self.be.increment)

    def test_context_mgr(self):
        with self.be as count:
            self.assertEqual(count, 1)

        self.assertEqual(self.be.value, 0)
        assert not self.inc.assert_has_calls([
            mock.call(1),
            mock.call(-1)
        ])

    def test_decrement(self):
        value = self.be.decrement()
        self.assertEqual(value, -1)
        self.inc.assert_called_once_with(-1)
