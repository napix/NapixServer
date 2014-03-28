#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

from napixd.managers import Manager

from napixd.services.urls import URL
from napixd.services.served import (
    FirstServedManager,
    ServedManager,
    ServedAction,
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
        self.nx_c = mock.Mock()

    def fsm(self):
        return FirstServedManager(
            self.mc,
            self.conf,
            self.url,
            self.ns,
            self.lock)

    def test_instantiate(self):
        fsm = self.fsm()
        m = fsm.instantiate(None, self.nx_c)

        self.mc.assert_called_once_with(None, self.nx_c)
        self.assertEqual(m, self.mc.return_value)
        m.configure.assert_called_once_with(self.conf)

    def test_resource_fields(self):
        self.assertEqual(self.fsm().resource_fields, {
            'abc': {
                'example': 123,
            },
        })

    def test_source(self):
        self.assertEqual(self.fsm().source, {
            'class': 'MyManager',
            'module': __name__,
            'file': __file__,
        })

    def test_get_all_actions(self):
        self.mc.get_all_actions.return_value = ['action']
        fsm = self.fsm()
        self.assertEqual(fsm.get_all_actions(), [
            ServedAction(fsm, 'action')
        ])


class TestServedManager(unittest.TestCase):
    def setUp(self):
        self.mc = mock.MagicMock(
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
        self.nx_c = mock.Mock()
        self.extractor = mock.Mock()

    def sm(self):
        return ServedManager(
            self.mc,
            self.conf,
            self.url,
            self.ns,
            self.extractor,
            self.lock)

    def test_instantiate(self):
        sm = self.sm()
        r = mock.Mock()
        m = sm.instantiate(r, self.nx_c)

        self.mc.assert_called_once_with(self.extractor.return_value, self.nx_c)
        self.assertEqual(m, self.mc.return_value)
        m.configure.assert_called_once_with(self.conf)
        self.extractor.assert_called_once_with(r)
