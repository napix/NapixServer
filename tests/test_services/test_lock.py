#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mock
import unittest

from napixd.conf import Conf
from napixd.utils.lock import Lock
from napixd.services.lock import (
    LockFactory,
    ConnectionFactory,
)


class TestLockFactory(unittest.TestCase):
    def setUp(self):
        self.cf = mock.Mock(
            spec=ConnectionFactory,
        )
        self.lock_class = mock.Mock(spec=Lock)

    def lf(self):
        return LockFactory(self.cf, lock_class=self.lock_class)

    def test_lock_factory(self):
        conf = Conf({
            'name': u'the-lock',
        })
        lock = self.lf()(conf)
        self.assertEqual(lock, self.lock_class.return_value)
        self.lock_class.assert_called_once_with(
            'the-lock', self.cf.return_value)
        self.cf.assert_called_once_with(conf)

    def test_expects_name(self):
        conf = Conf({})
        self.assertRaises(TypeError, self.lf(), conf)
