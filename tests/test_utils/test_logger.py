#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

import logging

from napixd.utils.logger import (
    ColoredLineFormatter,
    ColoredLevelFormatter,
)


class TestColoredFormatter(unittest.TestCase):
    def setUp(self):
        self.r = logging.makeLogRecord({
            'levelno': logging.INFO,
            'levelname': 'INFO',
            'msg': 'pif %s pouf',
            'args': ('paf',),
        })

    def test_line(self):
        clf = ColoredLineFormatter('%(levelname)s %(message)s', colors={
            'INFO': 32,
        })
        line = clf.format(self.r)
        self.assertEqual(line, '\033[1;32mINFO pif paf pouf\033[0m')

    def test_level(self):
        clf = ColoredLevelFormatter('%(levelname)s %(message)s', colors={
            'INFO': 32,
        })
        line = clf.format(self.r)
        self.assertEqual(line, '\033[1;32mINFO\033[0m pif paf pouf')
