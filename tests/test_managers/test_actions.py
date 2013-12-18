#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.managers.base import ManagerType, Manager
from napixd.managers.actions import action


class TestManagerAction(unittest.TestCase):
    def setUp(self):
        @action
        def send_mail(self, resource, dest, subject='export'):
            """send a mail"""
            return dest, subject
        self.fn = send_mail
        self.Manager = ManagerType('NewManager', (Manager, ), {
            'send_mail': self.fn,
            'get_resource': mock.Mock(spec=True, return_value={'mpm': 'prefork'}),
        })

    def test_class_with_actions(self):
        self.assertEqual(self.Manager.get_all_actions(), ['send_mail'])
