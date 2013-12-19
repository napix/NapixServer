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


class TestConnectionFactory(unittest.TestCase):
    def setUp(self):
        self.con_class = mock.Mock()
        self.conf = Conf({})

    def cf(self):
        return ConnectionFactory(
            connection_class=self.con_class,
            default_conf=self.conf,
        )

    def test_call_default(self):
        cf = self.cf()
        con = cf(Conf({}))
        self.assertEqual(con, self.con_class.return_value)
        self.con_class.assert_called_once_with(
            host=u'localhost',
            port=6379,
            db=2,
        )

    def test_call_custom_host(self):
        self.conf = Conf({
            'host': u'redis.napix.io',
            'port': '4444',
        })
        cf = self.cf()
        cf(Conf({
            'host': u'redis1.napix.io'
        }))
        self.con_class.assert_called_once_with(
            host='redis1.napix.io',
            port=6379,
            db=2,
        )
