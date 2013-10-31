#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest2
import mock

from napixd.conf import Conf
from napixd.managers.base import ManagerType, Manager
from napixd.managers.actions import action, parameter
from napixd.services.collection import FirstCollectionService


class _TestDecorator(unittest2.TestCase):

    def setUp(self):
        @action
        def send_mail(self, resource, dest, subject='export'):
            """send a mail"""
            return dest, subject
        self.fn = send_mail


class _TestManagerAction(_TestDecorator):

    def setUp(self):
        super(_TestManagerAction, self).setUp()
        self.Manager = ManagerType('NewManager', (Manager, ), {
            'send_mail': self.fn,
            'get_resource': mock.Mock(spec=True, return_value={'mpm': 'prefork'}),
        })


class TestManagerAction(_TestManagerAction):

    def test_class_with_actions(self):
        self.assertEqual(self.Manager.get_all_actions(), ['send_mail'])


class _TestServiceAction(_TestManagerAction):

    def setUp(self):
        super(_TestServiceAction, self).setUp()
        self.cs = FirstCollectionService(self.Manager, Conf(), 'my-mock')


class TestServiceAction(_TestServiceAction):

    def test_set_bottle(self):
        bottle = mock.Mock()
        self.cs.setup_bottle(bottle)
        self.assertSetEqual(
            set(mc[0][0] for mc in bottle.route.call_args_list),
            set([
                '/my-mock',
                '/my-mock/',
                '/my-mock/?',
                '/my-mock/_napix_help',
                '/my-mock/_napix_resource_fields',
                '/my-mock/?/_napix_all_actions',
                '/my-mock/?/_napix_action/send_mail',
                '/my-mock/?/_napix_action/send_mail/_napix_help',
                ]))

    def test_all_action(self):
        all_actions = self.cs.as_list_actions('id')
        self.assertEqual(all_actions, ['send_mail'])
