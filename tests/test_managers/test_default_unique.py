#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.managers.default import ReadOnlyUniqueManager, UniqueManager
from napixd.services.wrapper import ResourceWrapper
from napixd.exceptions import NotFound


random = mock.Mock()


class RandomManager(ReadOnlyUniqueManager):
    resource_fields = {
        'value': {
            'type': float,
            'computed': True,
            'description': 'A random number between 0 an 1',
        }
    }

    def load(self, context):
        return {
            'value': random(context)
        }


class TestROUM(unittest.TestCase):
    def setUp(self):
        self.context = mock.Mock()
        self.request = mock.Mock()
        self.rm = RandomManager(self.context, self.request)

    def tearDown(self):
        random.reset_mock()

    def test_name(self):
        self.assertEqual(self.rm.NAME, 'random')

    def test_list_resource(self):
        self.assertEqual(self.rm.list_resource(), ['random'])

    def test_get_resource_not_found(self):
        self.assertRaises(NotFound, self.rm.get_resource, 'something')
        self.assertEqual(random.call_count, 0)

    def test_get_resource(self):
        self.assertEqual(self.rm.get_resource('random'),
                         {'value': random.return_value})
        random.assert_called_once_with(self.context)


class PRNGSeedManager(UniqueManager):
    NAME = 'seed'

    resource_fields = {
        'seed': {
            'type': long,
            'description': 'The raw seed',
            'example': 2143L
        }
    }

    def load(self, context):
        return {'seed': random.get_seed()}

    def save(self, context, resource):
        random.set_seed(resource['seed'])


class TestUM(unittest.TestCase):
    def setUp(self):
        self.context = mock.Mock()
        self.request = mock.Mock()
        self.sm = PRNGSeedManager(self.context, self.request)

    def tearDown(self):
        random.reset_mock()

    def test_name(self):
        self.assertEqual(self.sm.NAME, 'seed')

    def test_update(self):
        self.sm.modify_resource(
            ResourceWrapper(self.sm, 'seed', {'seed': 123L}),
            {'seed': 1456L})
        random.set_seed.assert_called_once_with(1456)
