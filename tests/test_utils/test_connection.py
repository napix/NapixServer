#!/usr/bin/env python
# -*- coding: utf-8 -*-


import mock
import unittest

from napixd.conf import Conf

from napixd.utils.connection import (
    ConnectionFactory,
    transaction,
    WatchError,
)


class TestConnectionFactory(unittest.TestCase):
    def setUp(self):
        self.con_class = mock.Mock()
        self.conf = Conf({})

    def cf(self):
        return ConnectionFactory(
            self.conf,
            connection_class=self.con_class,
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


class Test_transaction(unittest.TestCase):
    def setUp(self):
        self.cb = mock.Mock(name='callback')
        self.con = mock.MagicMock(name='connection')
        self.pipe = self.con.pipeline.return_value.__enter__.return_value
        self.tcb = transaction(self.con)(self.cb)

    def test_arguments(self):
        self.tcb(1, 2, a='b')
        self.cb.assert_called_once_with(self.pipe, 1, 2, a='b')

    def test_watch_error(self):
        self.pipe.execute.side_effect = [WatchError(), True]

        self.tcb()
        self.cb.assert_has_calls([
            mock.call(self.pipe),
            mock.call(self.pipe),
        ])

    def test_execute(self):
        self.cb.return_value = self.pipe
        self.assertEqual(self.tcb(), self.pipe.execute.return_value)
        self.pipe.execute.assert_called_once_with()
