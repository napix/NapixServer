#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.managers.base import ManagerType, Manager
from napixd.managers.mixins import AttrResourceMixin

class TestMixinSerialize(unittest.TestCase):
    def setUp(self):
        self.Manager = ManagerType('Serializable', ( AttrResourceMixin, Manager), {
            'resource_fields': {
                'a': {
                    'example': 1
                },
                'b': {
                    'example': 'abc'
                }
            }
        })

    def test_serialize(self):
        mgr = self.Manager(None)
        serialized = mgr.serialize(mock.Mock(a=2, b='def'))
        self.assertEqual(serialized, {'a': 2, 'b': 'def'})
