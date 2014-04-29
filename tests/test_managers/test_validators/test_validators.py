#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

from napixd.exceptions import ValidationError
from napixd.managers.validators import (
    MatchRegexp,
    not_empty,
    StringValidator,
)


class TestStringValidator(unittest.TestCase):
    def test_not_empty_empty(self):
        self.assertRaises(ValidationError, not_empty, '')

    def test_not_empty(self):
        self.assertEqual(not_empty('value'), 'value')

    def test_strip_multiline(self):
        sv = StringValidator(strip=True, multiline=False)
        self.assertEqual(sv(' value\n\n'), 'value')

    def test_multiline(self):
        sv = StringValidator(strip=False, multiline=False)
        self.assertRaises(ValidationError, sv, ' value\n\n')

    def test_strip_empty(self):
        sv = StringValidator(strip=True, empty=False, multiline=False)
        self.assertRaises(ValidationError, sv, '\n\n\n')




class TestMatchRegexp(unittest.TestCase):

    def setUp(self):
        with mock.patch('re.compile') as Regexp:
            self.match_re = MatchRegexp('/^a[123]$/',
                                        error='Error because of {value}',
                                        docstring='Match a1, a2, a3')
        self.re = Regexp.return_value

    def test_doctstring(self):
        self.assertEqual(self.match_re.__doc__, 'Match a1, a2, a3')

    def test_re_pass(self):
        self.re.match.return_value = True
        self.assertEqual(self.match_re('a1'), 'a1')

    def test_re_fail(self):
        self.re.match.return_value = None
        self.assertRaises(ValidationError, self.match_re, 'a2')
