#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from napixd.services.urls import URL


class TestURL(unittest.TestCase):

    def test_url_noargs(self):
        url = URL()
        self.assertEqual(unicode(url), u'/')

    def test_url_args(self):
        url = URL(['ab', None])
        self.assertEqual(unicode(url), u'/ab/:f0')

    def test_add_segment(self):
        url = URL(['ab', None])
        url = url.add_segment('cd')
        self.assertEqual(unicode(url), u'/ab/:f0/cd')

    def test_add_variable(self):
        url = URL(['ab', None])
        url = url.add_variable()
        self.assertEqual(unicode(url), u'/ab/:f0/:f1')

    def test_reverse(self):
        url = URL(['ab', None, 'cd', None])
        self.assertEqual(url.reverse(['a/b', 'cd']), u'/ab/a%2Fb/cd/cd')

    def test_reverse_additional(self):
        url = URL(['ab', None, 'cd', None])
        self.assertEqual(
            url.reverse(['a/b', 'cd', 'ef']), u'/ab/a%2Fb/cd/cd/ef')

    def test_reverse_empty(self):
        url = URL(['ab'])
        self.assertEqual(url.reverse([]), u'/ab')

    def test_with_slash(self):
        url = URL(['ab', None])
        self.assertEqual(url.with_slash(), '/ab/:f0/')
