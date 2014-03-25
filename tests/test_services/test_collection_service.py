#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import unittest

from napixd.managers import Manager
from napixd.services import ServedManager, ServedAction
from napixd.services.urls import URL
from napixd.services.wrapper import ResourceWrapper
from napixd.http.request import Request
from napixd.http.server import WSGIServer as Server

from napixd.services.collection import (
    CollectionService,
    FirstCollectionService,
    ActionService
)


class TestFirstCollectionService(unittest.TestCase):
    def setUp(self):
        self.request = mock.Mock(spec=Request)
        self.all_actions = []
        self.Manager = mock.Mock(
            spec=Manager,
            get_managed_classes=mock.Mock(return_value=[]),
        )
        self.conf = mock.Mock()
        self.served_manager = mock.Mock(
            spec=ServedManager,
            configuration=self.conf,
            manager_class=self.Manager,
            url=URL(['parent']),
            lock=None,
            get_all_actions=mock.Mock(return_value=self.all_actions),
        )

    @property
    def fcs(self):
        return FirstCollectionService(self.served_manager)

    def add_action(self):
        a = mock.Mock(
            spec=ServedAction,
            lock=None,
        )
        a.name = 'impulse'
        self.all_actions.append(a)
        return a

    def test_get_managers(self):
        managers, manager = self.fcs.get_managers([], self.request)

        self.assertEqual(managers, [])
        self.assertEqual(manager, self.served_manager.instantiate.return_value)

    def test_as_meta(self):
        self.assertEqual(self.fcs.as_help(self.request),
                         self.served_manager.meta_data)

    def test_as_resource_fields(self):
        self.assertEqual(self.fcs.as_resource_fields(self.request),
                         self.served_manager.resource_fields)

    def test_as_example(self):
        self.assertEqual(self.fcs.as_example_resource(self.request),
                         self.Manager.get_example_resource.return_value)

    def test_as_list_action_empty(self):
        self.assertEqual(self.fcs.as_list_actions(self.request), [])

    def test_as_list_action(self):
        self.add_action()
        self.assertEqual(self.fcs.as_list_actions(self.request), ['impulse'])

    def test_setup_bottle(self):
        server = mock.Mock(spec=Server)
        fcs = self.fcs
        fcs.setup_bottle(server)

        server.route.assert_has_calls([
            mock.call(u'/parent/_napix_resource_fields', fcs.as_resource_fields),
            mock.call(u'/parent/_napix_help', fcs.as_help),
            mock.call(u'/parent', mock.ANY),
            mock.call(u'/parent/', fcs.as_collection),
            mock.call(u'/parent/?', fcs.as_resource),
        ], any_order=True)

    def test_setup_bottle_actions(self):
        server = mock.Mock(spec=Server)
        self.add_action()
        fcs = self.fcs
        fcs.setup_bottle(server)

        server.route.assert_has_calls([
            mock.call(u'/parent/_napix_resource_fields', fcs.as_resource_fields),
            mock.call(u'/parent/_napix_help', fcs.as_help),
            mock.call(u'/parent', mock.ANY),
            mock.call(u'/parent/', fcs.as_collection),
            mock.call(u'/parent/?', fcs.as_resource),
            mock.call(u'/parent/?/_napix_all_actions', fcs.as_list_actions),
        ], any_order=True)

    def test_setup_bottle_with_create(self):
        self.Manager.create_resource = mock.Mock()
        server = mock.Mock(spec=Server)
        fcs = self.fcs
        fcs.setup_bottle(server)

        server.route.assert_has_calls([
            mock.call(u'/parent/_napix_resource_fields', fcs.as_resource_fields),
            mock.call(u'/parent/_napix_help', fcs.as_help),
            mock.call(u'/parent', mock.ANY),
            mock.call(u'/parent/', fcs.as_collection),
            mock.call(u'/parent/?', fcs.as_resource),
            mock.call(u'/parent/_napix_new', fcs.as_example_resource),
        ], any_order=True)

    def test_setup_bottle_with_managed_classes(self):
        server = mock.Mock(spec=Server)
        self.Manager.get_managed_classes.return_value = [
            mock.Mock()
        ]
        fcs = self.fcs
        fcs.setup_bottle(server)

        server.route.assert_has_calls([
            mock.call(u'/parent/_napix_resource_fields', fcs.as_resource_fields),
            mock.call(u'/parent/_napix_help', fcs.as_help),
            mock.call(u'/parent', mock.ANY),
            mock.call(u'/parent/', fcs.as_collection),
            mock.call(u'/parent/?', fcs.as_resource),
            mock.call(u'/parent/?/', fcs.as_managed_classes),
        ], any_order=True)


class TestCollectionService(unittest.TestCase):
    def setUp(self):
        self.request = mock.Mock(spec=Request)
        self.all_actions = []
        self.Manager = mock.Mock(
            spec=Manager,
            name='Manager',
            get_managed_classes=mock.Mock(return_value=[]),
        )
        self.extractor = mock.Mock()
        self.conf = mock.Mock()
        self.served_manager = mock.Mock(
            spec=ServedManager,
            name='served_manager',
            configuration=self.conf,
            manager_class=self.Manager,
            url=URL(['parent']),
            lock=None,
            get_all_actions=mock.Mock(return_value=self.all_actions),
            extractor=self.extractor,
        )
        self.ps = mock.Mock(
            spec=CollectionService,
            name='previous_service',
        )

    @property
    def cs(self):
        return CollectionService(self.ps, self.served_manager)

    def test_generate_manager_fcs(self):
        pmgr = mock.Mock(name='PreviousManager', spec=Manager, get_resource=mock.Mock())
        self.ps.get_managers.return_value = ([], pmgr)

        managers, manager = self.cs.get_managers(['abc'], self.request)

        self.ps.get_managers.assert_called_once_with([], self.request)
        self.assertEqual(manager, self.served_manager.instantiate.return_value)
        self.assertEqual(managers, [
            (pmgr, ResourceWrapper(pmgr, pmgr.validate_id.return_value)),
        ])
        pmgr.get_resource.assert_called_once_with(pmgr.validate_id.return_value)
        pmgr.validate_id.assert_called_once_with('abc')


class TestActionService(unittest.TestCase):
    def setUp(self):
        self.request = mock.Mock(spec=Request)
        self.served_action = mock.Mock(
            spec=ServedAction,
            meta_data=mock.Mock(),
            name='served_action',
            lock=None,
        )
        self.served_action.name = 'impulse'
        self.collection_service = mock.Mock(
            spec=CollectionService,
            resource_url=URL(['parent', None]),
        )

    @property
    def acs(self):
        return ActionService(self.collection_service, self.served_action)

    def test_setup_bottle(self):
        server = mock.Mock(spec=Server)
        acs = self.acs
        acs.setup_bottle(server)

        server.route.assert_has_calls([
            mock.call('/parent/?/_napix_action/impulse/_napix_help', acs.as_help),
            mock.call('/parent/?/_napix_action/impulse', acs.as_action),
        ], any_order=True)

    def test_as_meta(self):
        self.assertEqual(self.acs.as_help(self.request),
                         self.served_action.meta_data)

    def test_get_managers(self):
        self.assertEqual(self.acs.get_managers(['id'], self.request),
                         self.collection_service.get_managers.return_value)
