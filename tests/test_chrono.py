#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import time
import mock

from napixd.chrono import Chrono


class TestChrono(unittest.TestCase):

    def test_chrono_running(self):
        chrono = Chrono()
        with chrono:
            self.assertAlmostEquals(chrono.total, .0, places=2)
            time.sleep(.1)
            self.assertAlmostEquals(chrono.total, .1, places=2)

    def test_chrono(self):
        chrono = Chrono()
        with chrono:
            time.sleep(.1)
        self.assertAlmostEquals(chrono.total, .1, places=2)

    def test_chrono_exception(self):
        chrono = Chrono()
        try:
            with chrono:
                time.sleep(.1)
                raise Exception
        except:
            pass
        self.assertAlmostEquals(chrono.total, .1, places=2)

    def test_repr(self):
        chrono = Chrono()
        self.assertEqual(repr(chrono), '<Chrono unstarted>')
        with mock.patch('time.time', side_effect=[100, 110, 120]):
            with chrono:
                self.assertEqual(repr(chrono), '<Chrono for 10>')
        self.assertEqual(repr(chrono), '<Chrono 20>')
