#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

import datetime

from napixd.exceptions import ValidationError
from napixd.managers.validators.date import (
    ISO8601_datetime,
    ISO8601_date,
    DatetimeBoundary,
)


class TestISO8601(unittest.TestCase):
    def test_datetime(self):
        self.assertEqual(ISO8601_datetime('2014-10-01T05:06:14'),
                         datetime.datetime(2014, 10, 1, 5, 6, 14))

    def test_date(self):
        self.assertEqual(ISO8601_date('2014-10-01'),
                         datetime.date(2014, 10, 1))

    def test_bad_date(self):
        self.assertRaises(ValidationError, ISO8601_date, '2014-13-01')

    def test_bad_datetime(self):
        self.assertRaises(ValidationError, ISO8601_datetime, '2014-01-01Tabcd')


class TestDatetimeBoundary(unittest.TestCase):
    def setUp(self):
        self.direction = 'future'
        self.past = datetime.datetime(2012, 6, 15, 12, 15, 00)
        self.now = datetime.datetime(2013, 6, 15, 12, 15, 00)
        self.future = datetime.datetime(2014, 6, 15, 12, 15, 00)

    def expect_past(self):
        self.direction = 'past'

    def db(self):
        return DatetimeBoundary(
            allow_future=self.direction == 'future',
            allow_past=self.direction == 'past',
        )

    def check(self, date):
        db = self.db()
        with mock.patch('napixd.managers.validators.date.datetime') as dt:
            dt.datetime.now.return_value = self.now
            return db(date)

    def test_allow_future_future(self):
        self.assertEqual(self.check(self.future), self.future)

    def test_allow_future_past(self):
        self.assertRaises(ValidationError, self.check, self.past)

    def test_allow_past_future(self):
        self.expect_past()
        self.assertRaises(ValidationError, self.check, self.future)

    def test_allow_past_past(self):
        self.expect_past()
        self.assertEqual(self.check(self.past), self.past)

    def test_direction_init(self):
        self.assertEqual(DatetimeBoundary('future'),
                         DatetimeBoundary(allow_past=False))
        self.assertNotEqual(DatetimeBoundary('past'),
                            DatetimeBoundary(allow_past=False))
