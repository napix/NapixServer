#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import

import unittest
import mock

from napixd.utils.step import Steps


class TestSteps(unittest.TestCase):
    def setUp(self):
        self.f1 = mock.MagicMock(
            __name__='step1'
        )
        self.f2 = mock.MagicMock(
            __name__='step2'
        )

    def test_no_cb(self):
        step = Steps()
        f1 = step(self.f1)
        f2 = step(self.f2)

        f1()
        f2()
        self.assertEqual(step.progress, 1)

    def test_cb(self):
        cb = mock.Mock()
        step = Steps(cb=cb)
        f1 = step(self.f1)
        f2 = step(self.f2)

        f1()
        cb.assert_called_once_with(step)
        f2()
        self.assertEqual(cb.call_count, 2)
