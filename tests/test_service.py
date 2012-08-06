#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2

from mock.manager_types import Players
from mock.managed_class import Paragraphs,STORE
from mock.request import POST,PUT,GET,DELETE
from bases import TestServiceBase

from napixd.services import Service
from napixd.loader import NapixdBottle

class TestService(TestServiceBase):
    def setUp(self):
        self.bottle = NapixdBottle([ Service(Paragraphs) ],
                no_conversation=True)
        self.bottle.setup_bottle()

    def testGETCollection(self):
        self._expect_ok(GET('/p'))
        self._expect_list(GET('/p/'),['/p/mouse','/p/cat'])
        self._expect_list(GET('/p/mouse/'),['/p/mouse/a','/p/mouse/mouse','/p/mouse/sleeps'])
        self._expect_list(GET('/p/cat/eats/'),
                ['/p/cat/eats/l', '/p/cat/eats/t', '/p/cat/eats/_napix_all_actions' ])
        self._expect_list(GET('/p/cat/eats/_napix_all_actions'),
                [ 'split', 'reverse', 'hash' ])
        self._expect_list(GET('/p/cat/eats/l/'),
                ['/p/cat/eats/l/e', '/p/cat/eats/l/a', '/p/cat/eats/l/t','/p/cat/eats/l/s'])
        self._expect_list(GET('/p/mouse/sleeps/t/'),['/p/mouse/sleeps/t/french'])

    def testGETResource(self):
        self._expect_dict(GET('/p/mouse'),{'text':'a mouse sleeps'})
        self._expect_dict(GET('/p/mouse/sleeps'),{'word':'sleeps'})
        self._expect_dict(GET('/p/mouse/sleeps/l/e'),{'letter':'e'})
        self._expect_dict(GET('/p/mouse/sleeps/t/french'),
                {'translated':'dors','language':'french'})

    def testGETErrors(self):
        self._expect_error(GET('/p/lololol'),400)
        self._expect_error(GET('/p/bird'),404)

    def testPOSTErrors(self):
        self._expect_error(POST('/p/',text='that car is fast'),400)
        self._expect_error(POST('/p/',flip='this bird is far'),400)
        self._expect_error(POST('/p/',text='that mouse is black'),409)
        self._expect_error(POST('/p/',text='that bird '),400)

    def testPOSTCollection(self):
        self._expect_created(POST('/p/',text='the bird flies high'),'/p/bird')
        self.assertDictEqual(STORE['paragraphs']['bird'],{'text':'the bird flies high'})

    def testPOSTSubCollection(self):
        self._expect_created(POST('/p/cat/eats/t/', language='german', translated='isst' ),
                '/p/cat/eats/t/german')
        self.assertDictEqual(STORE['translations'], {
                    'french':{ 'translated':'mange', 'language':'french'},
                    'german':{  'translated':'isst', 'language':'german'}
                    })

    def testPUTResource(self):
        self._expect_ok(PUT('/p/mouse',text='the mouse is close'))
        self.assertDictEqual(STORE['paragraphs']['mouse'],{'text':'the mouse is close'})

    def testDELETEResource(self):
        self._expect_ok(DELETE('/p/mouse'))
        self.assertFalse('mouse' in STORE['paragraphs'])

    def testUnsupportedMethod(self):
        self._expect_405(POST('/p/cat/eats/l/e'),'HEAD,GET')
        self._expect_405(DELETE('/p/'),'HEAD,POST,GET')

    def testDocumentation(self):
        self._expect_dict(GET('/p/_napix_resource_fields'), {'text': {
            'description': 'Text of the story',
            'example': 'The quick brown fox jump over the lazy dog'}})

        self._expect_dict(GET('/p/_napix_new'),
                {'text': 'The quick brown fox jump over the lazy dog'})
        self._expect_dict(GET('/p/*/*/t/_napix_new'),{
            'language' : 'esperanto',
            'translated' : 'aferon'
            })
        actual_docs = self._request(GET('/p/*/_napix_help'))
        expected_docs = {
            'absolute_url' : '/p/*/*',
            'actions' :  {
                'hash' : 'Return the word hashed with the given function',
                'reverse' : 'Reverse the word',
                'split' : 'Extract the start from a string'
                },
            'collection_methods': ['HEAD', 'GET'],
            'doc': 'Words of each paragrach',
            'human': '/_napix_autodoc/p.html',
            'direct_plug' : False,
            'managed_class': ['l', 't'],
            'resource_fields': {'word': {
                'description' : 'A word in the story',
                }},
            'resource_methods': ['HEAD', 'GET']}
        for key, value in expected_docs.items():
            self.assertEqual( actual_docs[key], value)

    def testDocumentationError(self):
        self._expect_405(PUT('/p/*/_napix_resource_fields',
                newfields={'name':'robin'}),'HEAD,GET')

    def testStartEndRequest(self):
        request = GET('/p/mouse/sleeps/t/french')
        self._do_the_request( request)
        self.assertListEqual( request.mark, [ 'in_para', 'in_words', 'in_trans',
            'out_trans', 'out_words', 'out_para'])

class TestErrors(TestServiceBase):
    def setUp(self):
        self.bottle = NapixdBottle([ Service(Paragraphs) ],
                no_conversation = True)
        self.bottle.setup_bottle()

    def testSlash(self):
        self._expect_list(GET('/'), ['/p'])

    def testException(self):
        resp = self._expect_error(GET('/p/cat/cat/t/french'),500)
        filename = resp.output.pop('filename')
        traceback = resp.output.pop('traceback')
        self.assertTrue( filename.endswith( 'mock/managed_class.py' ))
        self.assertDictEqual(resp.output, {
            'error_text' : 'I don\'t like cats',
            'error_class': 'ValueError',
            'line' : 41,
            'request' : { 'method' : 'GET', 'path' : '/p/cat/cat/t/french'}
            })

class TestSerializers(TestServiceBase):
    def setUp(self):
        self.bottle = NapixdBottle([ Service(Players) ],
                no_conversation = True)
        self.bottle.setup_bottle()
    
    def test_serializer( self):
        resp = self._request( GET( '/players/1' ))
        self.assertEqual( resp['score'], '15.30')

    def test_unserializer(self):
        self._expect_created( POST( '/players/', name='koala', score='12.123'), '/players/str-float-')

    def test_object_bad_type(self):
        self._expect_error( POST( '/players/', name=[ 'koala' ], score=23.12), 400)


if __name__ == '__main__':
    unittest2.main()
