#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock


from napixd.services.contexts import (
    NapixdContext,
)


class TestNapixdContext(unittest.TestCase):
    def setUp(self):
        self.app = mock.Mock()
        self.req = mock.Mock()
        self.nx_c = NapixdContext(self.app, self.req)

    def test_get_service(self):
        self.assertEqual(self.nx_c.get_service('alias'), self.app.find_service.return_value)
        self.app.find_service.assert_called_once_with('alias')
