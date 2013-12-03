#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import unittest2

from napixd.conf import Conf
from napixd.services import CollectionService, FirstCollectionService
from napixd.managers.managed_classes import ManagedClass
from napixd.http.request import Request

from tests.mock.managers import Manager, Managed


class TestCollectionServiceManaged(unittest2.TestCase):

    def setUp(self):
        Managed.reset_mock()
        Manager.reset_mock()
        self.fcs_conf = mock.Mock(spec=Conf, name='fcs_conf')
        self.cs_conf = mock.Mock(spec=Conf, name='cs_conf')
        self.fcs = FirstCollectionService(Manager, self.fcs_conf, 'parent', None)
        self.managed_class = mock.Mock(
            spec=ManagedClass, manager_class=Managed)
        self.managed_class.extractor.side_effect = lambda x: x
        self.cs = CollectionService(
            self.fcs, self.managed_class, self.cs_conf, 'child', None)

    def test_as_colletction(self):
        r = mock.Mock(spec=Request, method='GET')
        with mock.patch('napixd.services.collection.ServiceCollectionRequest') as SCR:
            self.fcs.as_collection(r, 'p1', 'c2')

        SCR.assert_called_once_with(r, ['p1', 'c2'], self.fcs)

    def test_as_resource(self):
        r = mock.Mock(spec=Request, method='GET')
        with mock.patch('napixd.services.collection.ServiceResourceRequest') as SRR:
            self.fcs.as_resource(r, 'p1')

        SRR.assert_called_once_with(r, ['p1'], self.fcs)

    def test_as_managed_classes(self):
        r = mock.Mock(spec=Request, method='GET')
        with mock.patch('napixd.services.collection.ServiceManagedClassesRequest') as SMCR:
            managed_classes_url = self.fcs.as_managed_classes(r, 'p1')

        SMCR.assert_called_once_with(r, ['p1'], self.fcs)
        self.assertEqual(managed_classes_url, SMCR.return_value.handle.return_value)

    def test_get_managers(self):
        managed = Managed.return_value
        manager = Manager.return_value
        all, this = self.cs.get_managers(['p1'], mock.Mock(spec=Request))
        self.assertEqual(managed, this)

        self.assertEqual(len(all), 1)
        manager_, wrapped = all[0]
        self.assertEqual(manager, manager_)
        manager.configure.assert_called_once_with(self.fcs_conf)
        manager.validate_id.assert_called_once_with('p1')
        self.assertEqual(wrapped.id, manager.validate_id())
        manager.get_resource.assert_called_once_with(wrapped.id)
        self.assertEqual(wrapped.resource, manager.get_resource())

    def test_generate_manager(self):
        resource = mock.Mock()
        request = mock.Mock(spec=Request)
        self.cs.generate_manager(resource, request)
        self.managed_class.extractor.assert_called_once_with(resource)
        Managed.assert_called_once_with(resource, request)

    def test_get_name_fcs(self):
        self.assertEqual(self.fcs.get_name(), 'parent')

    def test_get_name_cs(self):
        self.assertEqual(self.cs.get_name(), 'parent.child')
