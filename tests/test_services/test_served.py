#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

from napixd.managers import Manager

from napixd.services.urls import URL
from napixd.services.contexts import ResourceContext
from napixd.services.served import (
    FirstServedManager,
    ServedManager,
    ServedAction,
    ServedManagerInstance,
)


class TestFirstServedManager(unittest.TestCase):
    def setUp(self):
        self.action = mock.MagicMock(
            __name__='action',
        )
        self.mc = mock.MagicMock(
            __name__='MyManager',
            __module__=__name__,
            spec=Manager,
            get_all_actions=mock.Mock(),
            action=self.action,
            _resource_fields={
                'abc': {
                    'example': 123,
                },
            }
        )
        self.conf = mock.Mock()
        self.url = URL(['parent'])
        self.ns = ('parent',)
        self.lock = None
        self.nx_c = mock.Mock(name='napix_context')
        self.mc.get_all_actions.return_value = ['action']
        self.fsm = FirstServedManager(
            self.mc,
            self.conf,
            self.url,
            self.ns,
            self.lock)

    def test_context(self):
        m = self.fsm.instantiate(None, self.nx_c)
        self.assertEqual(
            m,
            ServedManagerInstance(
                self.mc.return_value,
                ResourceContext(self.fsm, self.nx_c))
        )

    def test_instantiate(self):
        self.fsm.instantiate(None, self.nx_c)
        self.mc.assert_called_once_with(None, ResourceContext(self.fsm, self.nx_c))

    def test_resource_fields(self):
        self.assertEqual(self.fsm.resource_fields, {
            'abc': {
                'example': 123,
            },
        })

    def test_source(self):
        self.assertEqual(self.fsm.source, {
            'class': 'MyManager',
            'module': __name__,
            'file': __file__,
        })

    def test_get_all_actions(self):
        self.assertEqual(self.fsm.get_all_actions(), [
            ServedAction(self.fsm, 'action')
        ])


class TestServedManager(unittest.TestCase):
    def setUp(self):
        self.mc = mock.MagicMock(
            name='Manager',
            __name__='MyManager',
            __module__=__name__,
            spec=Manager,
            _resource_fields={
                'abc': {
                    'example': 123,
                },
            }
        )
        self.conf = mock.Mock()
        self.url = URL(['parent'])
        self.ns = ('parent',)
        self.lock = None
        self.nx_c = mock.Mock(name='napix_context')
        self.extractor = mock.Mock()
        self.resource = mock.Mock(name='resource')
        self.sm = ServedManager(
            self.mc,
            self.conf,
            self.url,
            self.ns,
            self.extractor,
            self.lock)

    def instantiate(self):
        return self.sm.instantiate(self.resource, self.nx_c)

    def test_configure(self):
        m = self.instantiate()
        m.configure.assert_called_once_with(self.conf)

    def test_extractor(self):
        self.instantiate()
        self.mc.assert_called_once_with(self.extractor.return_value, mock.ANY)
        self.extractor.assert_called_once_with(self.resource)

    def test_context(self):
        m = self.instantiate()
        self.assertEqual(
            m,
            ServedManagerInstance(
                self.mc.return_value,
                ResourceContext(self.sm, self.nx_c))
        )


class TestServedManagerInstance(unittest.TestCase):
    def setUp(self):
        self.instance = mock.Mock()
        self.instance.validate_id.side_effect = lambda x: x
        self.context = mock.Mock(
            spec=ResourceContext,
        )
        self.smi = ServedManagerInstance(
            self.instance,
            self.context,
        )

    def test_set_manager(self):
        self.assertEqual(self.context.manager, self.instance)

    def test_validate_id(self):
        id_ = self.smi.validate_id('abc')

        self.assertEqual(id_, 'abc')
        self.instance.validate_id.assert_called_once_with('abc')

        self.assertEqual(self.context.id, 'abc')

    def test_get_resource(self):
        self.smi.validate_id('abc')
        r = self.smi.get_resource()
        self.assertEqual(r, self.context.make_resource.return_value)
        self.instance.get_resource.assert_called_once_with('abc')
