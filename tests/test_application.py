#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import

import unittest
import mock

from napixd.application import NapixdBottle
from napixd.services import Service
from napixd.loader import Loader, Load


class TestNapixBottleBuilder(unittest.TestCase):

    def test_napix_bottle(self):
        loader = mock.Mock(spec=Loader)
        load = loader.load.return_value = mock.Mock(spec=Load)
        with mock.patch.object(NapixdBottle, 'make_services') as make_s:
            NapixdBottle(loader)

        make_s.assert_called_once_with(load.managers)

    def test_make_services(self):
        loader = mock.Mock(spec=Loader)
        load = loader.load.return_value = mock.Mock(spec=Load)
        load.managers = []
        bottle = NapixdBottle(loader)

        m1 = mock.Mock()
        m2 = mock.Mock()
        load.managers = [m1, m2]

        with mock.patch('napixd.application.Service', spec=Service) as pService:
            s1, s2 = pService.side_effect = [
                mock.Mock(name='s1', spec=Service, url='m1'),
                mock.Mock(name='s2', spec=Service, url='m2'),
            ]

            bottle.make_services(load.managers)

        self.assertEqual(bottle.root_urls, set(['m1', 'm2']))

        pService.assert_has_calls([
            mock.call(m1.manager, m1.alias, m1.config),
            mock.call(m2.manager, m2.alias, m2.config),
        ])

        s1.setup_bottle.assert_called_once_with(bottle)
        s2.setup_bottle.assert_called_once_with(bottle)

        self.assertEqual(bottle.slash(), ['/m1', '/m2'])


class MyService(object):

    def __init__(self, mgr, alias, conf):
        self.alias = alias
        self.url = self.alias

    def setup_bottle(self, app):
        app.route('/' + self.url, callback=self.keep)
        app.route('/' + self.url + '/', callback=self.keep)
        app.route('/' + self.url + '/:f1', callback=self.keep)

    def keep(self):
        pass


class TestReload(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.patch_service = mock.patch('napixd.application.Service', MyService)

    def setUp(self):
        self.Service = self.patch_service.start()
        loader = mock.Mock(spec=Loader)
        self.load = load = loader.load.return_value = mock.Mock(spec=Load)
        m1 = mock.Mock(alias='m1')
        m2 = mock.Mock(alias='m2')
        load.managers = [m1, m2]
        load.new_managers = []
        load.old_managers = []
        load.error_managers = []

        self.bottle = NapixdBottle(loader)

        load.managers = []
        self.ms = mock.patch.object(
            self.bottle, 'make_services',
            side_effect=self.bottle.make_services).start()

    def tearDown(self):
        self.patch_service.stop()

    def test_zero(self):
        self.assertEqual(len(self.bottle.routes), 7)
        self.assertEqual(self.bottle.root_urls, set(['m1', 'm2']))

    def test_reload_new(self):
        m3 = mock.Mock(alias='m3')

        self.load.new_managers = [m3]
        self.bottle.reload()

        self.ms.assert_called_once_with([m3])

        self.assertEqual(len(self.bottle.routes), 10)
        self.assertEqual(self.bottle.root_urls, set(['m1', 'm2', 'm3']))

    def test_reload_old(self):
        self.load.old_managers = [mock.Mock(alias='m2')]
        self.bottle.reload()

        self.assertEqual(len(self.bottle.routes), 4)
        self.ms.assert_called_once_with([])
        self.assertEqual(self.bottle.root_urls, set(['m1']))

    def test_reload_error(self):
        error = mock.Mock(alias='m2')
        self.load.old_managers = [mock.Mock(alias='m2')]
        self.load.error_managers = [error]

        self.bottle.reload()

        self.assertEqual(len(self.bottle.routes), 7)
        self.ms.assert_called_once_with([])
        self.assertEqual(self.bottle.root_urls, set(['m1', 'm2']))
