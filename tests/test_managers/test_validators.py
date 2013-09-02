#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

from napixd.exceptions import ValidationError
from napixd.managers.validators import MatchRegexp

class TestMatchRegexp(unittest.TestCase):
    def setUp(self):
        with mock.patch('re.compile') as Regexp:
            self.match_re = MatchRegexp('/^a[123]$/',
                                        error='Error because of {value}',
                                        docstring='Match a1, a2, a3')
        self.re = Regexp.return_value

    def test_doctstring(self):
        self.assertEqual(self.match_re.__help__, 'Match a1, a2, a3')

    def test_re_pass(self):
        self.re.match.return_value = True
        self.assertEqual(self.match_re('a1'), 'a1')

    def test_re_fail(self):
        self.re.match.return_value = None
        self.assertRaises(ValidationError, self.match_re, 'a2')

