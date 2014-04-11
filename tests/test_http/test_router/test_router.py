#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
import mock

from napixd.http.router.step import URLTarget
from napixd.http.router.router import FilterResolved, Router


class TestFilterResolved(unittest.TestCase):
    def test_callback(self):
        cb = mock.Mock()
        filter = mock.Mock()
        request = mock.Mock()

        fr = FilterResolved(cb, filter)
        self.assertEqual(fr(request), filter.return_value)
        filter.assert_called_once_with(cb, request)


class TestRouter(unittest.TestCase):
    def setUp(self):
        with mock.patch('napixd.http.router.router.RouterStep') as RS:
            self.router = Router()
        self.rs = RS.return_value

    def test_contains(self):
        self.assertEqual('/a/b' in self.router, self.rs.__contains__.return_value)
        self.rs.__contains__.assert_called_once_with(URLTarget('/a/b'))

    def test_no_filter(self):
        resolved = self.router.resolve('/a/b/c')
        self.rs.resolve.assert_called_once_with(URLTarget('/a/b/c'))
        self.assertEqual(resolved, self.rs.resolve.return_value)

    def test_no_filter_none(self):
        self.rs.resolve.return_value = None
        resolved = self.router.resolve('/a/b/c')
        self.assertEqual(resolved, None)

    def test_filter(self):
        filter = mock.Mock()
        self.router.add_filter(filter)
        resolved = self.router.resolve('/a/b/c')
        self.assertEqual(resolved, FilterResolved(self.rs.resolve.return_value, filter))

    def test_filter_none(self):
        self.rs.resolve.return_value = None
        resolved = self.router.resolve('/a/b/c')
        self.rs.resolve.assert_called_once_with(URLTarget('/a/b/c'))
        self.assertEqual(resolved, None)

    def test_route(self):
        cb = mock.Mock()
        self.router.route('/a/b/c', cb)
        self.rs.route.assert_called_once_with(URLTarget('/a/b/c'), cb, False)

    def test_route_non_callable(self):
        cb = mock.NonCallableMock()
        self.assertRaises(ValueError, self.router.route, '/a/b/c', cb)

    def test_unroute(self):
        self.router.unroute('/a/b/c')
        self.rs.unroute.assert_called_once_with(URLTarget('/a/b/c'), all=False)
