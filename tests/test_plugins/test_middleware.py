#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

from napixd.plugins.middleware import (
    HTTPHostMiddleware,
)


class TestHTTPHostMiddleware(unittest.TestCase):
    def setUp(self):
        self.app = mock.Mock()
        self.hosts = ['hostname']
        self.sr = mock.Mock()

    def hhm(self):
        return HTTPHostMiddleware(self.hosts, self.app)

    def test_good_host(self):
        hhm = self.hhm()

        resp = hhm({
            'HTTP_HOST': 'hostname',
        }, self.sr)
        self.assertEqual(resp, self.app.return_value)

    def test_bad_host(self):
        hhm = self.hhm()

        resp = hhm({
            'HTTP_HOST': 'other',
        }, self.sr)
        self.assertEqual(self.app.call_count, 0)
        self.assertEqual(resp, ['Bad host'])

        assert not self.sr.assert_called_once_with('400 Bad Request', mock.ANY)
