#!/usr/bin/env python
# -*- coding: utf-8 -*-


import mock
import unittest

from napixd.conf import Conf

from napixd.utils.connection import ConnectionFactory


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
