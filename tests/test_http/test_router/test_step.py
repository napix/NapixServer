#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
import mock

from napixd.http.router.step import RouterStep, RouteTaken, URLTarget, ResolvedRequest


class TestURLTarget(unittest.TestCase):
    def test_nonzero(self):
        target = URLTarget('/')
        self.assertTrue(bool(target))
        next(target)
        self.assertFalse(bool(target))

    def test_add_argument(self):
        target = URLTarget('/dest/in/ation')
        target.add_argument('in')
        self.assertEqual(target.arguments, ['in'])

    def test_remaining(self):
        target = URLTarget('/dest/in/ation')
        self.assertEqual(target.remaining, 'dest/in/ation')
        next(target)
        self.assertEqual(target.remaining, 'in/ation')


class TestResolvedRequest(unittest.TestCase):
    def setUp(self):
        self.cb = mock.Mock()
        self.request = mock.Mock()

    def test_no_args(self):
        rr = ResolvedRequest(self.cb, [])
        rr(self.request)
        self.cb.assert_called_once_with(self.request)

    def test_args(self):
        rr = ResolvedRequest(self.cb, ['a', 'b', 'c'])
        rr(self.request)
        self.cb.assert_called_once_with(self.request, 'a', 'b', 'c')


class TestRouterStep(unittest.TestCase):
    def setUp(self):
        self.rs = RouterStep()
        self.cb = mock.Mock()

    def test_empty(self):
        self.assertFalse(self.rs)

    def test_truth_has_own_route(self):
        self.rs.route(URLTarget('/'), mock.Mock())
        self.assertTrue(self.rs)

    def test_truth_has_route(self):
        self.rs.route(URLTarget('/a/b/c/d'), mock.Mock())
        self.assertTrue(self.rs)

    def test_route_static(self):
        self.rs.route(URLTarget('/a/b'), self.cb)
        self.assertEqual(self.rs.resolve(URLTarget('/a/b')),
                         ResolvedRequest(self.cb, []))

    def test_route_dynamic(self):
        self.rs.route(URLTarget('/a/?'), self.cb)
        self.assertEqual(self.rs.resolve(URLTarget('/a/b')),
                         ResolvedRequest(self.cb, ['b']))

    def test_re_route_static(self):
        self.rs.route(URLTarget('/a/b'), self.cb)
        self.assertRaises(RouteTaken, self.rs.route, URLTarget('/a/b'), self.cb)

    def test_re_route_dynamic(self):
        self.rs.route(URLTarget('/a/?'), self.cb)
        self.assertRaises(RouteTaken, self.rs.route, URLTarget('/a/?'), self.cb)

    def test_resolve_no_route(self):
        self.rs.route(URLTarget('/a/b'), self.cb)
        self.assertEqual(self.rs.resolve(URLTarget('/a/c')), None)

    def test_resolve_no_route_intermediate(self):
        self.rs.route(URLTarget('/a/b/c'), self.cb)
        self.assertEqual(self.rs.resolve(URLTarget('/a/b')), None)

    def test_resolve_no_route_under(self):
        self.assertEqual(self.rs.resolve(URLTarget('/a/c')), None)

    def test_resolve_slash(self):
        self.rs.route(URLTarget('/a/'), self.cb)
        self.assertEqual(self.rs.resolve(URLTarget('/a/')),
                         ResolvedRequest(self.cb, []))

    def test_unroute(self):
        self.rs.route(URLTarget('/a/'), self.cb)
        self.rs.route(URLTarget('/a/b'), self.cb)

        self.rs.unroute(URLTarget('/a/'))
        self.assertTrue(self.rs.resolve(URLTarget('/a/')) is None)
        self.assertFalse(self.rs.resolve(URLTarget('/a/b')) is None)

    def test_unroute_reroute(self):
        self.rs.route(URLTarget('/a/'), self.cb)
        self.rs.unroute(URLTarget('/a/'))
        self.rs.route(URLTarget('/a/'), self.cb)
        self.assertFalse(self.rs.resolve(URLTarget('/a/')) is None)

    def test_unroute_all(self):
        self.rs.route(URLTarget('/a/'), self.cb)
        self.rs.route(URLTarget('/a/b'), self.cb)

        self.rs.unroute(URLTarget('/a'), all=True)
        self.assertTrue(self.rs.resolve(URLTarget('/a/')) is None)
        self.assertTrue(self.rs.resolve(URLTarget('/a/b')) is None)


class TestContains(unittest.TestCase):
    def setUp(self):
        self.rs = rs = RouterStep()
        cb = mock.Mock()
        rs.route(URLTarget('/a/'), cb)
        rs.route(URLTarget('/a/b'), cb)
        rs.route(URLTarget('/a/?'), cb)
        rs.route(URLTarget('/c/?/d'), cb)

    def test_contains_1(self):
        self.assertTrue(URLTarget('/a/') in self.rs)

    def test_contains_2(self):
        self.assertTrue(URLTarget('/a/b') in self.rs)

    def test_contains_3(self):
        self.assertTrue(URLTarget('/a/?') in self.rs)

    def test_contains_4(self):
        self.assertTrue(URLTarget('/c/?/d') in self.rs)

    def test_not_contains_1(self):
        self.assertFalse(URLTarget('/a') in self.rs)

    def test_not_contains_2(self):
        self.assertFalse(URLTarget('/a/c') in self.rs)

    def test_not_contains_3(self):
        self.assertFalse(URLTarget('/c/?') in self.rs)

    def test_not_contains_4(self):
        self.assertFalse(URLTarget('/c/?/') in self.rs)

    def test_not_contains_5(self):
        self.assertFalse(URLTarget('/d/') in self.rs)


class TestCatchallRouterStep(unittest.TestCase):
    def setUp(self):
        self.rs = RouterStep()
        self.cb = mock.MagicMock(
            __name__='callback'
        )

    def test_route_root(self):
        self.rs.route(URLTarget('/a/'), self.cb, catchall=True)
        self.assertEqual(self.rs.resolve(URLTarget('/a/')),
                         ResolvedRequest(self.cb, ['']))

    def test_route_path(self):
        self.rs.route(URLTarget('/a/'), self.cb, catchall=True)
        self.assertEqual(self.rs.resolve(URLTarget('/a/b/c')),
                         ResolvedRequest(self.cb, ['b/c']))

    def test_reroute(self):
        self.rs.route(URLTarget('/a/'), self.cb)
        self.assertRaises(RouteTaken, self.rs.route,
                          URLTarget('/a/'), self.cb, catchall=True)

    def test_route_dynamic_path(self):
        self.rs.route(URLTarget('/a/?/'), self.cb, catchall=True)
        self.assertEqual(self.rs.resolve(URLTarget('/a/b/c/d')),
                         ResolvedRequest(self.cb, ['b', 'c/d']))

    def test_re_route(self):
        self.rs.route(URLTarget('/a/?'), self.cb)
        self.assertRaises(RouteTaken, self.rs.route,
                          URLTarget('/a/'), self.cb, catchall=True)

    def test_route_inside(self):
        self.rs.route(URLTarget('/a/'), self.cb, catchall=True)
        self.assertRaises(RouteTaken, self.rs.route, URLTarget('/a/?/b/'), self.cb)

    def test_unroute(self):
        self.rs.route(URLTarget('/a/'), self.cb, catchall=True)
        self.rs.unroute(URLTarget('/a/'))
        self.assertTrue(self.rs.resolve(URLTarget('/a/b/c')) is None)

    def test_unroute_inside(self):
        self.rs.route(URLTarget('/a/'), self.cb, catchall=True)
        self.rs.unroute(URLTarget('/a/?/c'))
        self.assertFalse(self.rs.resolve(URLTarget('/a/b/c')) is None)

    def test_unroute_all(self):
        self.rs.route(URLTarget('/a/'), self.cb)
        self.rs.route(URLTarget('/a/b'), self.cb)

        self.rs.unroute(URLTarget('/a'), all=True)
        self.assertTrue(self.rs.resolve(URLTarget('/a/')) is None)
        self.assertTrue(self.rs.resolve(URLTarget('/a/b')) is None)

    def test_contains(self):
        self.rs.route(URLTarget('/a/'), self.cb, catchall=True)
        self.assertTrue(URLTarget('/a/') in self.rs)

    def test_not_contains(self):
        self.rs.route(URLTarget('/a/'), self.cb, catchall=True)
        self.assertFalse(URLTarget('/a/d') in self.rs)
        self.assertFalse(URLTarget('/a/?/d') in self.rs)
        self.assertFalse(URLTarget('/a/?') in self.rs)
