#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest2
import sys
import os


test_dir = os.path.dirname(sys.argv[0])
test_suite = unittest2.defaultTestLoader.discover(test_dir)
unittest2.TextTestRunner().run(test_suite)
