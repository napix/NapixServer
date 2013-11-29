#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.http.request import Request
from napixd.http.response import HTTPError

from napixd.auth.plugin import AAAPlugin


class TestAuthPlugin(unittest.TestCase):
    def setUp(self):
        self.request = mock.Mock(spec=Request, environ={})
        self.source = s = mock.Mock(return_value=None)
        self.sources = [s]
        self.provider = p = mock.Mock(return_value=None)
        self.providers = [p]
        self.cb = mock.Mock()

    def get_plugin(self):
        return AAAPlugin(self.sources, self.providers, timed=False)

    def call(self):
        p = self.get_plugin()
        return p(self.cb, self.request)

    def test_extraction(self):
        s1 = mock.Mock(return_value={'a': 1})
        self.sources.append(s1)
        p1 = mock.Mock(return_value=True)
        self.providers.append(p1)

        f = self.call()

        self.source.assert_called_once_with(self.request)
        self.provider.assert_called_once_with(self.request, s1.return_value)

        s1.assert_called_once_with(self.request)
        p1.assert_called_once_with(self.request, s1.return_value)
        self.assertEqual(f, self.cb.return_value)

    def test_not_extraction(self):
        s1 = mock.Mock(return_value=None)
        self.sources.append(s1)

        self.assertRaises(HTTPError, self.call)
        self.assertEqual(self.cb.call_count, 0)

    def test_authenticate(self):
        self.source.return_value = {'a': 1}
        self.provider.return_value = None

        self.assertRaises(HTTPError, self.call)
        self.assertEqual(self.cb.call_count, 0)

    def test_authenticate_fail(self):
        self.source.return_value = {'a': 1}
        self.provider.return_value = False

        self.assertRaises(HTTPError, self.call)
        self.assertEqual(self.cb.call_count, 0)

    def test_authenticate_filter(self):
        self.source.return_value = {'a': 1}
        self.provider.return_value = f = mock.Mock()

        check = self.call()

        self.assertEqual(check, f.return_value)
        f.assert_called_once_with(self.cb.return_value)
