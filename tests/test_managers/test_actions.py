#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock
import types

from napixd.managers.base import ManagerType, Manager
from napixd.managers.actions import action, parameter


class TestManagerAction(unittest.TestCase):
    def setUp(self):
        def send_mail(self, resource, dest, subject='export'):
            """send a mail"""
            return dest, subject

        #Like a duck
        self.fn = mock.MagicMock(
            __name__=send_mail.__name__,
            __doc__=send_mail.__doc__,
            spec=types.FunctionType,
            func_code=send_mail.func_code,
        )

        self.action = action(self.fn)
        self.Manager = ManagerType('MyManager', (Manager, ), {
            'send_mail': self.action,
            'get_resource': mock.Mock(spec=True, return_value={'mpm': 'prefork'}),
        })

    def test_class_with_actions(self):
        self.assertEqual(self.Manager.get_all_actions(), ['send_mail'])

    def test_action_class_property(self):
        a = self.Manager.send_mail
        self.assertEqual(a.__doc__, 'send a mail')
        self.assertEqual(a.__name__, 'send_mail')

    def test_action_instance_property(self):
        m = self.Manager(mock.Mock(), mock.Mock())
        r = mock.Mock()
        m.send_mail(r, 123, mpm='prefork')
        self.fn.assert_called_once_with(m, r, 123, mpm='prefork')

    def test_uba_rf(self):
        with mock.patch('napixd.managers.actions.ResourceFieldsDict') as RFD:
            uba = self.action.__get__(None, mock.Mock())
        RFD.assert_called_once_with(self.fn, self.action.resource_fields)
        self.assertEqual(uba.resource_fields, RFD.return_value)


class TestAction(unittest.TestCase):
    def actionize(self, fn, *args, **kw):
        pa = parameter(*args, **kw)(fn)
        with mock.patch('napixd.managers.actions.ResourceFields') as RF:
            action(pa)
        return RF

    def test_parameter_mandatory(self):
        def a(self, r, abc):
            pass

        RF = self.actionize(a, 'abc', example=123)
        RF.assert_called_once_with({
            'abc': {
                'example': 123,
                'optional': False,
            }
        })

    def test_parameter_optional(self):
        def a(self, r, abc=123):
            pass
        RF = self.actionize(a, 'abc', example=123)
        RF.assert_called_once_with({
            'abc': {
                'typing': 'static',
                'example': 123,
                'optional': True,
            }
        })

    def test_parameter_optional_none(self):
        def a(self, r, abc=None):
            pass
        RF = self.actionize(a, 'abc', example=123)
        RF.assert_called_once_with({
            'abc': {
                'typing': 'dynamic',
                'example': 123,
                'optional': True,
            }
        })
