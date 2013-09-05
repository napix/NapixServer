#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import time

from napixd.chrono import Chrono


class TestChrono(unittest.TestCase):
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
