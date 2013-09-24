#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import unittest
import mock
import sys

import napixd
from napixd import find_home


class TestHOME(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.orig = napixd.HOME
        try:
            self.prefix = sys.real_prefix
        except AttributeError:
            pass

    @classmethod
    def tearDownClass(self):
        napixd.HOME = self.orig
        try:
            sys.real_prefix = self.prefix
        except AttributeError:
            pass

    def setUp(self):
        try:
            del sys.real_prefix
        except AttributeError:
            pass

    def test_find_venv(self):
        #The project is installed in a venv.
        #returns this venv
        with mock.patch('sys.prefix', '/abc/def'):
            sys.real_prefix = '/usr'
            self.assertEqual(
                find_home('napixd', '/abc/def/libs/site-packages/napixd/__init__.py'),
                '/abc/def')

    def test_find_source(self):
        #The project is in its source directory
        #The venv is in the project dir
        with mock.patch('sys.prefix', '/abc/def/NapixServer/venv'):
            sys.real_prefix = '/usr'
            self.assertEqual(
                find_home('napixd', '/abc/def/NapixServer/napixd/__init__.py'),
                '/abc/def/NapixServer')

    def test_find_env(self):
        #The path is forced by a env variable
        with mock.patch('os.environ', {'NAPIXHOME': '/jkl/def'}):
            self.assertEqual(
                find_home('napixd', '/abc/def/NapixServer/napixd/__init__.py'),
                '/jkl/def')
