#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import unittest

from napixd.managers import Manager
from napixd.services.served import ServedManager, ServedAction
from napixd.services.urls import URL
from napixd.services.wrapper import ResourceWrapper
from napixd.services.contexts import NapixdContext, CollectionContext

from napixd.http.router.router import Router
from napixd.http.request import Request
from napixd.http.server import WSGIServer as Server

from napixd.services.collection import (
    CollectionService,
    FirstCollectionService,
    ActionService,
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

    def test_get_manager(self):
        fcs = self.fcs
        manager = fcs.get_manager([], self.request)
        self.served_manager.instantiate.assert_called_once_with(None, self.request)
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
        pmgr.validate_id.side_effect = lambda x: x
        self.ps.get_manager.return_value = pmgr
        pmgr.get_resource.return_value = pr = ResourceWrapper(pmgr, 'abc')

        manager = self.cs.get_manager(['abc'], self.request)

        self.ps.get_manager.assert_called_once_with([], self.request)

        self.served_manager.instantiate.assert_called_once_with(pr, self.request)
        self.assertEqual(manager, self.served_manager.instantiate.return_value)
        pmgr.get_resource.assert_called_once_with('abc')
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

    def test_get_manager(self):
        self.assertEqual(self.acs.get_manager(['id'], self.request),
                         self.collection_service.get_manager.return_value)


class TestServerCollectionService(unittest.TestCase):
    def setUp(self):
        self.context = mock.Mock(
            name='request',
            spec=NapixdContext,
            method='GET',
            parameters=mock.MagicMock(),
        )
        self.served_manager = mock.Mock(
            spec=ServedManager,
            name='served_manager',
            url=URL(['parent', None, 'child']),
            manager_class=mock.Mock(),
            lock=None,
            get_all_actions=mock.Mock(return_value=[]),
        )
        self.ps = mock.Mock(
            name='previous_service',
        )
        self.cs = CollectionService(self.ps, self.served_manager)
        self.router = Router()
        self.cs.setup_bottle(self.router)

    def test_as_resource(self):
        r = self.router.resolve('/parent/123/child/456')
        with mock.patch('napixd.services.collection.ServiceResourceRequest') as SR:
            resp = r(self.context)
        self.assertEqual(resp, SR.return_value.handle.return_value)
        SR.assert_called_once_with(CollectionContext(self.cs, self.context), [u'123', u'456'])

    def test_as_collection(self):
        r = self.router.resolve('/parent/123/child/')
        with mock.patch('napixd.services.collection.ServiceCollectionRequest') as SR:
            resp = r(self.context)
        self.assertEqual(resp, SR.return_value.handle.return_value)
        SR.assert_called_once_with(CollectionContext(self.cs, self.context), [u'123', ])

    def test_as_managed_classes(self):
        r = self.router.resolve('/parent/123/child/456/')
        with mock.patch('napixd.services.collection.ServiceManagedClassesRequest') as SR:
            resp = r(self.context)
        self.assertEqual(resp, SR.return_value.handle.return_value)
        SR.assert_called_once_with(CollectionContext(self.cs, self.context), [u'123', u'456'])

    def test_noop(self):
        r = self.router.resolve('/parent/123/child')
        resp = r(self.context)
        self.assertEqual(resp, None)
