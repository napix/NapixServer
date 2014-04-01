#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import

import unittest
import mock

from napixd.exceptions import InternalRequestFailed
from napixd.application import Napixd
from napixd.services.contexts import NapixdContext
from napixd.loader.loader import Loader, Load
from napixd.http.router.router import Router
from napixd.http.request import Request


class MyService(object):

    def __init__(self, mgr, alias, conf=None):
        self.alias = alias
        self.url = self.alias

    def setup_bottle(self, app):
        app.route('/' + self.url, self.keep)

    def keep(self):
        pass

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.alias == other.alias


class TestReload(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.patch_service = mock.patch('napixd.application.Service', MyService)

    def setUp(self):
        self.Service = self.patch_service.start()
        loader = mock.Mock(spec=Loader)
        self.load = load = loader.load.return_value = mock.Mock(spec=Load)
        self.m1 = m1 = mock.Mock(alias='m1')
        self.m2 = m2 = mock.Mock(alias='m2')
        load.managers = [m1, m2]
        load.new_managers = []
        load.old_managers = []
        load.error_managers = []

        self.server = server = mock.Mock(spec=Router)

        self.napixd = Napixd(loader, server)
        load.managers = []

    def tearDown(self):
        self.patch_service.stop()

    def test_add_filter(self):
        self.server.add_filter.assert_called_once_with(self.napixd)

    def test_as_plugin(self):
        cb = mock.Mock()
        req = mock.Mock()
        r = self.napixd(cb, req)
        self.assertEqual(r, cb.return_value)
        cb.assert_called_once_with(NapixdContext(self.napixd, req))

    def test_find_service(self):
        s = self.napixd.find_service('m1')
        self.assertEqual(s, MyService(None, 'm1'))

    def test_find_not_service(self):
        self.assertRaises(InternalRequestFailed, self.napixd.find_service, 'm3')

    def test_zero(self):
        assert not self.server.route.assert_has_calls([
            mock.call('/', self.napixd.slash),
            mock.call('/m1', mock.ANY),
            mock.call('/m2', mock.ANY),
        ])
        self.assertEqual(self.napixd.slash(mock.Mock(spec=Request)),
                         ['/m1', '/m2'])

    def test_reload_new(self):
        assert not self.server.route.reset_mock()
        m3 = mock.Mock(alias='m3')

        self.load.new_managers = [m3]
        self.napixd.reload()

        self.server.route.assert_called_once_with('/m3', mock.ANY)
        self.assertEqual(self.server.unroute.call_count, 0)
        self.assertEqual(self.napixd.slash(mock.Mock(spec=Request)),
                         ['/m1', '/m2', '/m3'])

    def test_reload_old(self):
        self.server.route.reset_mock()
        self.load.old_managers = [mock.Mock(alias='m2')]
        self.napixd.reload()

        self.server.unroute.assert_called_once_with('/m2', all=True)
        self.assertEqual(self.server.route.call_count, 0)
        self.assertEqual(self.napixd.slash(mock.Mock(spec=Request)),
                         ['/m1'])

    def test_reload_error(self):
        self.server.route.reset_mock()

        error = mock.Mock(alias='m2')
        self.load.old_managers = [mock.Mock(alias='m2')]
        self.load.error_managers = [error]

        self.napixd.reload()

        self.server.unroute.assert_called_once_with('/m2', all=True)
        self.server.route.assert_has_calls([
            mock.call('/m2', mock.ANY),
            mock.call('/m2/', mock.ANY, catchall=True),
        ])
        self.assertEqual(self.napixd.slash(mock.Mock(spec=Request)),
                         ['/m1', '/m2'])
