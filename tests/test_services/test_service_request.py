#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.managers.managed_classes import ManagedClass
from napixd.exceptions import ValidationError, NotFound, Duplicate
from napixd.services.urls import URL
from napixd.services.collection import (
    CollectionService,
    ActionService
)
from napixd.services.requests import (
    ServiceActionRequest,
    ServiceResourceRequest,
    ServiceCollectionRequest,
    ServiceManagedClassesRequest,
)
from napixd.services.wrapper import ResourceWrapper
from napixd.http.request import Request
from napixd.http.response import HTTP405, HTTPError


class TestServiceManagedClassesRequest(unittest.TestCase):
    def setUp(self):
        self.request = mock.Mock(spec=Request, method='GET')
        mc = mock.Mock(spec=ManagedClass)
        mc.get_name.return_value = 'def'
        self.manager = manager = mock.Mock()
        manager.get_managed_classes.return_value = [mc]
        self.url = url = URL(['abc', None])
        self.cs = mock.Mock(
            spec=CollectionService,
            lock=None,
            collection=manager,
            resource_url=url)
        self.cs.get_managers.return_value = ([], manager)

    def smcr(self):
        return ServiceManagedClassesRequest(self.request, ['123'], self.cs)

    def test_handle(self):
        self.assertEqual(self.smcr().handle(), ['/abc/123/def'])

    def test_handle_method(self):
        self.request.method = 'POST'
        self.assertRaises(HTTP405, self.smcr().handle)


def serialize(value):
    value['_s'] = True
    return value


class TestServiceCollectionRequest(unittest.TestCase):
    def setUp(self):
        self.request = mock.Mock(spec=Request, method='GET')
        self.request.GET = self.GET = {}
        self.manager = manager = mock.Mock()
        self.manager.serialize.side_effect = serialize
        self.url = url = URL(['abc', None])
        self.cs = mock.Mock(
            spec=CollectionService,
            lock=None,
            collection=manager,
            resource_url=url)
        self.cs.get_managers.return_value = ([], manager)

    def scr(self):
        return ServiceCollectionRequest(self.request, [], self.cs)

    def test_handle_other(self):
        self.request.method = 'DELETE'
        try:
            self.scr().handle()
        except HTTPError as e:
            self.assertEqual(e.status, 405)
            self.assertEqual(e.headers['Allow'], 'HEAD,GET,POST')
        else:
            self.fail()

    def test_handle_post(self):
        self.request.method = 'POST'
        self.manager.create_resource.return_value = 345

        r = self.scr().handle()

        self.assertEqual(r.status, 201)
        self.assertEqual(r.headers['Location'], '/abc/345')

        v = self.manager.validate
        v.assert_called_once_with(self.request.data, None)
        self.manager.create_resource.assert_called_once_with(v.return_value)

    def test_handle_post_conflict(self):
        self.request.method = 'POST'
        self.manager.create_resource.side_effect = Duplicate()
        try:
            self.scr().handle()
        except HTTPError as err:
            self.assertEqual(err.status, 409)
        else:
            self.fail()

    def test_handle_post_bad(self):
        self.request.method = 'POST'
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
        self.GET['getall'] = None
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
        self.GET['getall'] = None
        self.manager.get_all_resources.return_value = [
            {'mpm': 'prefork'},
            {'mpm': 'worker'},
        ]
        self.assertRaises(ValueError, self.scr().handle)

    def test_handle_getall_bad_bis(self):
        self.GET['getall'] = None
        self.manager.get_all_resources.return_value = None
        self.assertRaises(ValueError, self.scr().handle)

    def test_handle_head(self):
        self.request.method = 'HEAD'
        self.manager.list_resource.return_value = [678, 123]

        r = self.scr().handle()
        self.manager.list_resource.assert_called_once_with()

        self.assertEqual(r, None)

    def test_handle_get_filter(self):
        self.GET['nut_type'] = 'peanut'
        self.manager.list_resource_filter.return_value = [678, 123]

        r = self.scr().handle()
        self.manager.list_resource_filter.assert_called_once_with({'nut_type': 'peanut'})

        self.assertEqual(r, ['/abc/678', '/abc/123'])

    def test_handle_getall_filter(self):
        self.GET['getall'] = None
        self.GET['nut_type'] = 'peanut'

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


def validate_id(value):
    if value.isdigit():
        return int(value)
    raise ValidationError()


class TestServiceResourceRequest(unittest.TestCase):
    def setUp(self):
        self.request = mock.Mock(spec=Request, method='GET')
        self.request.GET = self.GET = {}
        self.manager = manager = mock.Mock()
        self.manager.validate_id.side_effect = validate_id
        self.manager.serialize.side_effect = serialize
        self.url = url = URL(['abc', None])
        self.cs = mock.Mock(
            spec=CollectionService,
            lock=None,
            collection=manager,
            resource_url=url)
        self.cs.get_managers.return_value = ([], manager)

    def srr(self):
        return ServiceResourceRequest(self.request, ['123'], self.cs)

    def test_handle_get(self):
        self.manager.get_resource.return_value = {'mpm': 'prefork'}
        r = self.srr().handle()
        self.assertEqual(r, {'mpm': 'prefork', '_s': True})

    def test_handle_get_None(self):
        self.manager.get_resource.return_value = None
        self.assertRaises(ValueError, self.srr().handle)


    def test_handle_get_404(self):
        self.manager.get_resource.side_effect = NotFound()
        try:
            self.srr().handle()
        except HTTPError as err:
            self.assertEqual(err.status, 404)
        else:
            self.fail()

    def test_handle_get_not_dict(self):
        self.manager.get_resource.return_value = mock.MagicMock()
        self.assertRaises(ValueError, self.srr().handle)

    def test_handle_put(self):
        self.request.method = 'PUT'
        self.manager.modify_resource.return_value = None

        r = self.srr().handle()
        self.assertEqual(r.status, 204)

        o = self.manager.get_resource.return_value
        v = self.manager.validate
        v.assert_called_once_with(self.request.data, o)
        self.manager.modify_resource.assert_called_once_with(
            ResourceWrapper(self.manager, 123, o),
            v.return_value
        )

    def test_handle_put_validation_error(self):
        self.request.method = 'PUT'
        self.manager.validate.side_effect = ValidationError({
            'mpm': 'This is prefork or worker'
        })

        try:
            self.srr().handle()
        except HTTPError as err:
            self.assertEqual(err.status, 400)
            self.assertEqual(err.body, {
                'mpm': 'This is prefork or worker'
            })
        else:
            self.fail()

    def test_handle_put_new_id(self):
        self.request.method = 'PUT'
        self.manager.modify_resource.return_value = 312

        r = self.srr().handle()
        self.assertEqual(r.status, 205)
        self.assertEqual(r.headers['Location'], '/abc/312')

    def test_handle_head(self):
        self.request.method = 'HEAD'
        self.manager.get_resource.return_value = {'mpm': 'prefork'}
        r = self.srr().handle()
        self.assertEqual(r, None)

    def test_handle_get_format_none(self):
        self.GET['format'] = 'pouet'
        o = self.manager.get_resource.return_value = {'mpm': 'prefork'}
        formatter = self.manager.get_formatter.return_value
        formatter.return_value = None

        r = self.srr().handle()

        formatter.assert_called_once_with(ResourceWrapper(self.manager, 123, o), r)

    def test_handle_get_format_not_exist(self):
        self.GET['format'] = 'pouet'
        self.manager.get_all_formats.return_value = {'this': '', 'that': ''}
        self.manager.get_formatter.side_effect = KeyError()

        r = self.srr().handle()
        self.assertEqual(r.status, 406)

    def test_handle_get_format_other_headers(self):
        self.GET['format'] = 'pouet'
        o = self.manager.get_resource.return_value = {'mpm': 'prefork'}

        def formatter(res, resp):
            resp.set_header('content-type', 'text/plain')
            self.assertEqual(res, ResourceWrapper(self.manager, 123, o))
            return 'pouetpouetpouet'
        self.manager.get_formatter.return_value.side_effect = formatter

        r = self.srr().handle()

        self.assertEqual(r.body, 'pouetpouetpouet')
        self.assertEqual(r.headers['Content-Type'], 'text/plain')

    def test_handle_delete(self):
        self.request.method = 'DELETE'
        self.srr().handle()
        self.manager.delete_resource.assert_called_once_with(
            ResourceWrapper(self.manager, 123))


class TestServiceActionRequest(unittest.TestCase):
    def setUp(self):
        self.request = mock.Mock(spec=Request, method='POST')
        self.request.GET = self.GET = {}
        self.manager = manager = mock.Mock()
        self.url = url = URL(['abc', None])
        self.acs = mock.Mock(
            spec=ActionService,
            collection=manager,
            resource_url=url)
        self.acs.get_managers.return_value = ([], manager)
        self.action = self.manager.do_the_stuff
        self.action.resource_fields.validate.return_value = {}

    def sar(self):
        return ServiceActionRequest(self.request, [123], self.acs, 'do_the_stuff')

    def test_handle(self):
        r = self.sar().handle()
        self.assertEqual(r, self.action.return_value)
