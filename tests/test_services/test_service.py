#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import unittest

from napixd.conf import Conf
from napixd.managers import Manager
from napixd.managers.managed_classes import ManagedClass
from napixd.exceptions import InternalRequestFailed

from napixd.services.urls import URL
from napixd.services.collection import (
    FirstCollectionService,
    CollectionService,
)
from napixd.services.served import (
    FirstServedManager,
    ServedManager,
)
from napixd.services import (
    Service,
)


class TestService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch_fcs = mock.patch('napixd.services.FirstCollectionService',
                                   spec=FirstCollectionService)
        cls.patch_cs = mock.patch('napixd.services.CollectionService',
                                  spec=CollectionService)

    def setUp(self):
        self.conf = mock.MagicMock(
            spec=Conf,
            name='Conf',
        )
        self.alias = 'parent'
        self.Manager = mock.Mock(
            spec=Manager,
            get_all_actions=mock.Mock(return_value=[]),
            get_managed_classes=mock.Mock(return_value=[]),
        )
        self.FCS = self.patch_fcs.start()
        self.CS = self.patch_cs.start()

    def tearDown(self):
        self.patch_fcs.stop()
        self.patch_cs.stop()

    def get_service(self):
        return Service(self.Manager, self.alias, self.conf)

    def add_managed_class(self):
        mgr = mock.Mock(
            spec=Manager,
            name='Managed',
            get_managed_classes=mock.Mock(return_value=[]),
        )
        mc = mock.Mock(
            spec=ManagedClass,
            manager_class=mgr,
            get_name=mock.Mock(return_value='child'),
        )
        self.Manager.get_managed_classes.return_value = [mc]
        self.FCS.return_value.resource_url = URL(['parent', None])
        return mc, mgr

    def test_get_collection_service(self):
        s = self.get_service()
        cs = s.get_collection_service(['parent'])
        self.assertEqual(cs, self.FCS.return_value)

    def test_get_collection_service_child(self):
        self.add_managed_class()
        s = self.get_service()
        cs = s.get_collection_service(['parent', 'child'])
        self.assertEqual(cs, self.CS.return_value)

    def test_get_collection_service_fail(self):
        s = self.get_service()
        self.assertRaises(InternalRequestFailed, s.get_collection_service, ['parent', 'that'])

    def test_FCS(self):
        self.get_service()
        self.FCS.assert_called_once_with(
            FirstServedManager(self.Manager, self.conf, ('parent',)),
            URL(['parent']))
        self.assertEqual(self.CS.call_count, 0)

    def test_setup_bottle(self):
        server = mock.Mock()
        s = self.get_service()
        s.setup_bottle(server)
        self.FCS.return_value.setup_bottle.assert_called_once_with(server)

    def test_CS(self):
        mc, mgr = self.add_managed_class()
        self.get_service()
        self.CS.assert_called_once_with(
            self.FCS.return_value,
            ServedManager(mgr, self.conf.get.return_value,
                          ('parent', 'child'),
                          extractor=mc.extractor),
            URL(['parent', None, 'child']))

        self.conf.get.assert_called_once_with('parent.child')

    def test_CS_lock(self):
        self.conf = Conf({
            'Lock': {
                'name': 'the-lock'
            }
        })
        mc, mgr = self.add_managed_class()
        with mock.patch('napixd.services.lock_factory') as LF:
            self.get_service()

        lock = LF.return_value

        self.FCS.assert_called_once_with(
            FirstServedManager(self.Manager, self.conf, ('parent', ), lock=lock), URL(['parent']))
        self.CS.assert_called_once_with(
            self.FCS.return_value,
            ServedManager(mgr, mock.ANY, ('parent', 'child'), mock.ANY, lock),
            URL(['parent', None, 'child']))

    def test_CS_bad_lock(self):
        self.conf = Conf({
            'Lock': {
            }
        })
        self.assertRaises(ValueError, self.get_service)
