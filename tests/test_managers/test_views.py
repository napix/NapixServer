#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import unittest2
import mock

from napixd.conf import Conf
from napixd.http import Response
from napixd.services import FirstCollectionService
from napixd.services.servicerequest import ServiceResourceRequest
from napixd.managers.base import ManagerType, Manager
from napixd.managers.views import view, content_type

class TestDecorators( unittest2.TestCase):
    def setUp(self):
        @view('text')
        def as_text( self, id, resource, response):
            response.write('oh snap')
        self.fn = as_text

    def test_set_view(self):
        self.assertEqual( self.fn._napix_view, 'text')

    def test_content_type(self):
        as_text = content_type( 'application/pip+pampoum')(self.fn)
        resp = mock.Mock()
        as_text( None, None, None, resp)
        resp.set_header.assert_called_once_with( 'Content-Type', 'application/pip+pampoum')

class TestManagerView(TestDecorators):
    def setUp(self):
        super( TestManagerView, self).setUp()
        self.manager = ManagerType( 'NewManager', ( Manager, ), {
            'as_text': self.fn,
            'get_resource' : mock.Mock(spec=True, return_value={ 'mpm': 'prefork' }),
            })
    def test_class_with_views(self):
        self.assertDictEqual( self.manager.get_all_formats(), { 'text' : self.fn })

    def test_class_with_inheritance(self):
        @view('xml')
        def as_xml():
            pass
        other_manager = ManagerType( 'NewManager', ( self.manager, ), {
            'as_xml': as_xml
            })

        self.assertDictEqual( other_manager.get_all_formats(), {
            'text' : self.fn,
            'xml' : as_xml,
            })
class TestServiceView( TestManagerView):
    def setUp( self):
        super( TestServiceView, self).setUp()
        self.cs = FirstCollectionService( self.manager, Conf(), 'child')

    def test_call_serializer(self):
        with mock.patch( 'bottle.request', method='GET', GET={ 'format': 'text' }):
            self.srr = ServiceResourceRequest([ 'p1', 'c2' ], self.cs)
            resp = self.srr.handle()
        self.assertIsInstance( resp, Response)
        resp.seek(0)
        self.assertEqual( resp.read(), 'oh snap')

    def test_call_unknown_serializer(self):
        with mock.patch( 'bottle.request', method='GET', GET={ 'format': 'png' }):
            self.srr = ServiceResourceRequest([ 'p1', 'c2' ], self.cs)
            resp = self.srr.handle()
        self.assertEqual( resp.status_code, 406)


