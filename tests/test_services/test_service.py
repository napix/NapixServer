#!/usr/bin/env pysource)
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import unittest2

from tests.mock.managers import Manager, Managed
from napixd.services import Service
from napixd.services.collection import BaseCollectionService
from napixd.conf import EmptyConf
from napixd.managers import ManagedClass


class TestServiceEmpty(unittest2.TestCase):

    def setUp(self):
        self.service = Service(Managed, 'my-mock', EmptyConf())

    def test_collection_service(self):
        self.assertTrue(all(isinstance(s, BaseCollectionService)
                            for s in self.service.collection_services))
        self.assertEqual(len(self.service.collection_services), 1)

    def test_set_bottle(self):
        bottle = mock.Mock()
        self.service.setup_bottle(bottle)
        self.assertSetEqual(
            set(mc[0][0] for mc in bottle.route.call_args_list),
            set([
                '/my-mock',
                '/my-mock/',
                '/my-mock/?',
                '/my-mock/_napix_help',
                '/my-mock/_napix_new',
                '/my-mock/_napix_resource_fields',
                ]))


class TestServiceWithManaged(unittest2.TestCase):

    def setUp(self):
        self.service = Service(Manager, 'this-mock', EmptyConf())

    def test_collection_service(self):
        self.assertTrue(all(isinstance(s, BaseCollectionService)
                            for s in self.service.collection_services))
        self.assertEqual(len(self.service.collection_services), 2)

    def test_set_bottle(self):
        bottle = mock.Mock()
        self.service.setup_bottle(bottle)
        self.assertSetEqual(
            set(mc[0][0] for mc in bottle.route.call_args_list),
            set([
                '/this-mock',
                '/this-mock/',
                '/this-mock/?',
                '/this-mock/_napix_help',
                '/this-mock/_napix_new',
                '/this-mock/_napix_resource_fields',
                '/this-mock/?/',
                '/this-mock/?/my-middle-mock',
                '/this-mock/?/my-middle-mock/',
                '/this-mock/?/my-middle-mock/?',
                '/this-mock/?/my-middle-mock/_napix_help',
                '/this-mock/?/my-middle-mock/_napix_new',
                '/this-mock/?/my-middle-mock/_napix_resource_fields',
                ]))
