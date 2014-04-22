#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock


from napixd.services.served import ServedManager
from napixd.services.wrapper import ResourceWrapper
from napixd.services.collection import CollectionService
from napixd.services.contexts import (
    CollectionContext,
    ResourceContext,
    NapixdContext,
    maybe,
)


class TestNapixdContext(unittest.TestCase):
    def setUp(self):
        self.app = mock.Mock()
        self.req = mock.Mock()
        self.nx_c = NapixdContext(self.app, self.req)

    def test_get_service(self):
        self.assertEqual(self.nx_c.get_service('alias'), self.app.find_service.return_value)
        self.app.find_service.assert_called_once_with('alias')


class TestCollectionContext(unittest.TestCase):
    def setUp(self):
        self.cs = mock.Mock(spec=CollectionService)
        self.context = mock.Mock()
        self.cc = CollectionContext(self.cs, self.context)

    def test_get_resource(self):
        Target_s = self.context.get_service
        Target_cs = Target_s.return_value.get_collection_service

        with mock.patch('napixd.services.contexts.FetchResource') as FR:
            with mock.patch('napixd.services.contexts.CollectionContext') as CC:
                self.cc.get_resource('/abc/123/def/456')

        FR.assert_called_once_with(CC.return_value, ['123', '456'])
        CC.assert_called_once_with(Target_cs.return_value, self.context, method='GET')
        Target_cs.assert_called_once_with(['abc', 'def'])
        Target_s.assert_called_once_with('abc')


class TestResourceContext(unittest.TestCase):
    def setUp(self):
        self.context = mock.Mock(
            spec=CollectionContext,
        )
        self.sm = mock.Mock(
            spec=ServedManager,
            namespaces=('abc', 'def'),
        )
        self.rc = ResourceContext(self.sm, self.context)
        self.rc.manager = mock.Mock()
        self.rc.id = mock.Mock()

    def test_resource_context(self):
        self.rc.resource = resource = mock.Mock()

        Cs = self.context.get_collection_service
        Manager = Cs.return_value.served_manager.instantiate

        sm = self.rc.get_sub_manager('alias')
        self.assertEqual(sm, Manager.return_value)
        Cs.assert_called_once_with(('abc', 'def', 'alias'))
        Manager.assert_called_once_with(resource, self.context)

    def test_resource_context_no_resource(self):
        resource = mock.Mock()

        Cs = self.context.get_collection_service
        Manager = Cs.return_value.served_manager.instantiate

        sm = self.rc.get_sub_manager('alias', resource)
        self.assertEqual(sm, Manager.return_value)
        Cs.assert_called_once_with(('abc', 'def', 'alias'))
        Manager.assert_called_once_with(
            ResourceWrapper(self.rc.manager, self.rc.id, resource), self.context)


class A(object):
    def __init__(self, x):
        self.x = x

    @maybe
    def a(self):
        self.x()


class TestMaybe(unittest.TestCase):
    def setUp(self):
        self.witness = mock.Mock()
        self.a = A(self.witness)

    def test_is_set(self):
        self.a.a = a = mock.Mock()
        self.assertEqual(self.a.a, a)

    def test_not_set(self):
        self.assertRaises(ValueError, lambda: self.a.a)
