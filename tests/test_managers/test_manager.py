#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import unittest
import mock

from napixd.exceptions import ValidationError, ImproperlyConfigured

from napixd.managers.base import Manager, ManagerType
from napixd.managers.managed_classes import ManagedClass
from napixd.managers.resource_fields import ResourceFieldsDescriptor
from napixd.managers.actions import action


class TestManager(unittest.TestCase):

    def setUp(self):
        self.manager = Manager({})
        self.resource_fields = mock.patch.object(
            self.manager, '_resource_fields', spec=ResourceFieldsDescriptor).start()

    def test_validate_id(self):
        self.assertEqual(self.manager.validate_id('12'), '12')

    def test_validate_id_raise(self):
        self.assertRaises(ValidationError, self.manager.validate_id, '')

    def test_validate_resource(self):
        v1 = mock.Mock()

        with mock.patch.object(self.manager, 'validate_resource') as vr:
            r = self.manager.validate(v1)

        self.resource_fields.validate.assert_called_once_with(v1, None)
        vr.assert_called_once_with(
            self.resource_fields.validate.return_value, None)
        self.assertEqual(r, vr.return_value)

    def test_detect(self):
        self.assertFalse(Manager.detect())


class TestManagerTypeDirectPlug(unittest.TestCase):

    class SubManager(Manager):
        pass

    def testNone(self):
        m = ManagerType('Manager', (Manager,), {
            'managed_class': None
        })
        self.assertEqual(m.get_managed_classes(), [])

    def testFalse(self):
        m = ManagerType('Manager', (Manager,), {
            'managed_class': [self.SubManager]
        })
        self.assertEqual(
            m.get_managed_classes(), [ManagedClass(self.SubManager)])

    def testFalseManagedClass(self):
        m = ManagerType('Manager', (Manager,), {
            'managed_class': [ManagedClass(self.SubManager, 'ploc')]
        })
        self.assertEqual(m.get_managed_classes(), [
                         ManagedClass(self.SubManager, 'ploc')])

    def testFalseString(self):
        m = ManagerType('Manager', (Manager,), {
            'managed_class': ['abc']
        })
        self.assertEqual(m.get_managed_classes(), [ManagedClass('abc')])

    def testTrue(self):
        self.assertRaises(ImproperlyConfigured, ManagerType,
                          'Manager', (Manager,), {
                              'managed_class': self.SubManager
                          })

    def testTrueString(self):
        self.assertRaises(ImproperlyConfigured, ManagerType,
                          'Manager', (Manager,), {
                              'managed_class': 'abc'
                          })

    def testTrueManagedClass(self):
        self.assertRaises(ImproperlyConfigured, ManagerType,
                          'Manager', (Manager,), {
                              'managed_class': ManagedClass('abc', 'ploc')
                          })


class TestManagerType(unittest.TestCase):

    def test_manager_rf(self):
        rf = mock.MagicMock(spec=dict)
        with mock.patch('napixd.managers.base.ResourceFields') as RF:
            m = ManagerType('Manager', (Manager,), {
                'resource_fields': rf
            })
        self.assertEqual(m._resource_fields, RF.return_value)
        RF.assert_called_once_with(rf)

    def test_inherit_actions(self):
        class M1(Manager):

            @action
            def a_m1(self, r):
                pass

        class M2(M1):

            @action
            def a_m2(self, r):
                pass

        self.assertEqual(M2.get_all_actions(), ['a_m1', 'a_m2'])
