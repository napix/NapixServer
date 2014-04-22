#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import unittest
import mock

from napixd.http.response import Response
from napixd.managers.base import ManagerType, Manager
from napixd.managers.views import view, content_type


class TestDecorators(unittest.TestCase):
    def test_set_view(self):
        @view('text', content_type='text/plain')
        def as_text(self, resource, response):
            response.write('oh snap')

        self.assertEqual(as_text._napix_view, 'text')

    def test_content_type_auto(self):
        @view('application/json')
        def as_text(self, resource, response):
            response.write('oh snap')

        self.assertEqual(as_text._napix_view, 'json')

        resp = mock.Mock(spec=Response, headers={})
        as_text(None, None, resp)
        resp.set_header.assert_called_once_with('Content-Type', 'application/json')

    def test_content_type_auto_json(self):
        @view('text')
        def as_text(self, resource, response):
            return {'value': 1}

        resp = mock.Mock(spec=Response, headers={})
        as_text(None, None, resp)
        self.assertEqual(resp.set_header.call_count, 0)

    def test_content_type_auto_unicode(self):
        @view('text')
        def as_text(self, resource, response):
            return u'dadà'

        resp = mock.Mock(spec=Response, headers={})
        as_text(None, None, resp)
        resp.set_header.assert_called_once_with('Content-Type', 'text/plain; charset=utf-8')

    def test_content_type_text_yaml(self):
        @view('yaml', content_type='text/yaml')
        def as_text(self, resource, response):
            return '''base:\n  '*':\n    station\n'''

        resp = mock.Mock(spec=Response, headers={})
        r = as_text(None, None, resp)
        resp.set_header.assert_called_once_with('Content-Type', 'text/yaml')
        self.assertEqual(r, '''base:\n  '*':\n    station\n''')

    def test_content_type(self):
        @view('text', content_type='text/plain')
        def as_text(self, resource, response):
            response.write('oh snap')

        resp = mock.Mock(spec=Response, headers={})
        as_text(None, None, resp)
        resp.set_header.assert_called_once_with('Content-Type', 'text/plain')

    def test_content_type_old(self):
        @view('text')
        @content_type('application/pip+pampoum')
        def as_text(self, resource, response):
            response.write('oh snap')

        resp = mock.Mock(spec=Response, headers={})
        as_text(None, None, resp)
        resp.set_header.assert_called_once_with('Content-Type', 'application/pip+pampoum')


class TestManagerView(unittest.TestCase):

    def setUp(self):
        @view('object')
        def as_object(self, resource, response):
            response.set_header('x-my-header', 'oh-snap')
            return {'a': 1}
        self.as_object = as_object

        self.manager = ManagerType('NewManager', (Manager, ), {
            'as_object': as_object
        })

    def test_class_with_views(self):
        self.assertEqual(self.manager.get_all_formats(), {
            'object': self.as_object,
        })

    def test_class_with_inheritance(self):
        @view('xml')
        def as_xml():
            pass
        other_manager = ManagerType('NewManager', (self.manager, ), {
            'as_xml': as_xml
        })

        self.assertEqual(other_manager.get_all_formats(), {
            'object': self.as_object,
            'xml': as_xml,
        })
