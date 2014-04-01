#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
import mock

from napixd.http.response import HTTPError
from napixd.exceptions import Duplicate

from napixd.services.urls import URL
from napixd.services.contexts import CollectionContext
from napixd.services.collection import CollectionService

from napixd.services.requests import (
    ServiceCollectionRequest,
)


def serialize(value):
    value['_s'] = True
    return value


class TestServiceCollectionRequest(unittest.TestCase):
    def setUp(self):
        self.manager = manager = mock.Mock()
        self.manager.serialize.side_effect = serialize
        self.url = url = URL(['abc', None])
        self.cs = mock.Mock(
            spec=CollectionService,
            lock=None,
            collection=manager,
            resource_url=url
        )
        self.context = mock.Mock(
            spec=CollectionContext,
            method='GET',
            parameters={},
            service=self.cs,
            data=mock.Mock(name='data'),
        )

        self.context.get_manager_instance.return_value = manager

    def scr(self):
        return ServiceCollectionRequest(self.context, [])

    def test_handle_other(self):
        self.context.method = 'DELETE'
        try:
            self.scr().handle()
        except HTTPError as e:
            self.assertEqual(e.status, 405)
            self.assertEqual(e.headers['Allow'], 'HEAD,GET,POST')
        else:
            self.fail()

    def test_handle_post(self):
        self.context.method = 'POST'
        self.manager.create_resource.return_value = 345

        r = self.scr().handle()

        self.assertEqual(r.status, 201)
        self.assertEqual(r.headers['Location'], '/abc/345')

        v = self.manager.validate
        v.assert_called_once_with(self.context.data, None)
        self.manager.create_resource.assert_called_once_with(v.return_value)

    def test_handle_post_conflict(self):
        self.context.method = 'POST'
        self.manager.create_resource.side_effect = Duplicate()
        try:
            self.scr().handle()
        except HTTPError as err:
            self.assertEqual(err.status, 409)
        else:
            self.fail()

    def test_handle_post_bad(self):
        self.context.method = 'POST'
        self.manager.create_resource.return_value = None
        self.assertRaises(ValueError, self.scr().handle)

    def test_handle_get(self):
        self.manager.list_resource.return_value = [678, 123]

        r = self.scr().handle()

        self.assertEqual(r, ['/abc/678', '/abc/123'])

    def test_handle_get_bad(self):
        self.manager.list_resource.return_value = None
        self.assertRaises(ValueError, self.scr().handle)

    def test_handle_getall(self):
        self.context.parameters['getall'] = None
        self.manager.get_all_resources.return_value = [
            [678, {'mpm': 'prefork'}],
            [345, {'mpm': 'worker'}],
        ]

        r = self.scr().handle()

        self.assertEqual(r, {
            '/abc/678': {'mpm': 'prefork', '_s': True},
            '/abc/345': {'mpm': 'worker', '_s': True},
        })

    def test_handle_getall_bad(self):
        self.context.parameters['getall'] = None
        self.manager.get_all_resources.return_value = [
            {'mpm': 'prefork'},
            {'mpm': 'worker'},
        ]
        self.assertRaises(ValueError, self.scr().handle)

    def test_handle_getall_bad_bis(self):
        self.context.parameters['getall'] = None
        self.manager.get_all_resources.return_value = None
        self.assertRaises(ValueError, self.scr().handle)

    def test_handle_head(self):
        self.context.method = 'HEAD'
        self.manager.list_resource.return_value = [678, 123]

        r = self.scr().handle()
        self.manager.list_resource.assert_called_once_with()

        self.assertEqual(r, None)

    def test_handle_get_filter(self):
        self.context.parameters['nut_type'] = 'peanut'
        self.manager.list_resource_filter.return_value = [678, 123]

        r = self.scr().handle()
        self.manager.list_resource_filter.assert_called_once_with({'nut_type': 'peanut'})

        self.assertEqual(r, ['/abc/678', '/abc/123'])

    def test_handle_getall_filter(self):
        self.context.parameters['getall'] = None
        self.context.parameters['nut_type'] = 'peanut'

        self.manager.get_all_resources_filter.return_value = [
            [678, {'mpm': 'prefork'}],
            [345, {'mpm': 'worker'}],
        ]

        r = self.scr().handle()

        self.manager.get_all_resources_filter.assert_called_once_with({
            'getall': None, 'nut_type': 'peanut'})
        self.assertEqual(r, {
            '/abc/678': {'mpm': 'prefork', '_s': True},
            '/abc/345': {'mpm': 'worker', '_s': True},
        })
