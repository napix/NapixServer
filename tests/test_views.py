#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bases import TestServiceBase
from mock.managed_class import Paragraphs
from mock.request import GET

from napixd.loader import NapixdBottle
from napixd.services import Service

class TestView(TestServiceBase):
    def setUp(self):
        self.bottle = NapixdBottle([ Service(Paragraphs) ],
                no_conversation=True, options=set())
        self.bottle.setup_bottle()

    def test_return_dict(self):
        req = GET( '/p/cat/cat/l/a')
        req.GET = { 'format' : 'otherapi' }
        self._expect_dict( req, { 'ascii' : 97, 'letter' : 'a', 'word' : 'cat' })

    def test_response(self):
        req = GET( '/p/cat/cat/l/a')
        req.GET = { 'format' : 'xml' }
        resp = self._request( req)
        resp.seek(0)
        self.assertEqual( resp.headers.get('Content-Type'), 'application/xml')
        self.assertEqual( resp.read(), '<letter ord="97">a</letter>')

    def test_response_empty(self):
        req = GET( '/p/cat/cat/l/a')
        req.GET = { 'format' : 'empty' }
        resp = self._request( req)
        self.assertEqual( resp.headers.get('my-own-header'), 'napix' )

    def test_unknow_format(self):
        req = GET( '/p/cat/cat/l/a')
        req.GET = { 'format' : 'non_existing' }
        resp = self._expect_error( req, 406)
        self.assertEqual( resp.output, 'Cannot render non_existing. Available formats are: xml,otherapi,empty ')


