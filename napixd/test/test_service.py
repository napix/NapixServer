#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
from napixd.test.mock.managed_class import Paragraphs,STORE
from napixd.test.mock.request import POST,PUT,GET,DELETE
from napixd.conf import Conf
from napixd.services import Service
from napixd.loader import NapixdBottle
import bottle

class TestServiceBase(object):
    def _do_the_request(self,request):
        bottle.request = request
        app,args = self.bottle.match(request.environ)
        return app.call(**args)
    def _request(self,request):
        try:
            return self._do_the_request(request)
        except bottle.HTTPError,e:
            self.fail(repr(e))
    def _expect_list(self,request,lst):
        self.assertListEqual(sorted(self._request(request)),sorted(lst))
    def _expect_dict(self,request,dct):
        resp = self._request(request)
        self.assertDictEqual(resp,dct)
    def _expect_error(self,request,code):
        try:
            resp = self._do_the_request(request)
        except bottle.HTTPError,e:
            self.assertEqual(e.status,code)
            return e
        else:
            self.fail('Unexpected %s'%repr(resp))
    def _expect_created(self,request,url):
        try:
            resp = self._do_the_request(request)
        except bottle.HTTPResponse,e:
            self.assertEqual(e.status, 202)
            self.assertEqual(e.headers['Location'],url)
        else:
            self.fail('Unexpected %s'%repr(resp))
    def _expect_ok(self,request):
        req = self._request(request)
        self.assertTrue(req is None)
    def _expect_405(self,request,expected_methods):
        resp = self._expect_error(request,405)
        expected_methods = set(expected_methods.split(','))
        actual_methods = set(resp.headers['Allow'].split(','))
        self.assertSetEqual(expected_methods,actual_methods)


class TestService(TestServiceBase, unittest2.TestCase):
    def setUp(self):
        self.bottle = NapixdBottle([ Service(Paragraphs,Conf({})) ])
        self.bottle.setup_bottle()

    def testGETCollection(self):
        self._expect_list(GET('/p/'),['/p/mouse','/p/cat'])
        self._expect_list(GET('/p/mouse/'),['/p/mouse/a','/p/mouse/mouse','/p/mouse/sleeps'])
        self._expect_list(GET('/p/cat/eats/'),['/p/cat/eats/l','/p/cat/eats/t'])
        self._expect_list(GET('/p/cat/eats/l/'),
                ['/p/cat/eats/l/e', '/p/cat/eats/l/a', '/p/cat/eats/l/t','/p/cat/eats/l/s'])
        self._expect_list(GET('/p/mouse/sleeps/t/'),['/p/mouse/sleeps/t/french'])

    def testGETResource(self):
        self._expect_dict(GET('/p/mouse'),{'text':'a mouse sleeps'})
        self._expect_dict(GET('/p/mouse/sleeps'),{'word':'sleeps','length':6})
        self._expect_dict(GET('/p/mouse/sleeps/l/e'),{'letter':'e','ord':101})
        self._expect_dict(GET('/p/mouse/sleeps/t/french'),
                {'translated':'dors','language':'french'})

    def testGETErrors(self):
        self._expect_error(GET('/p/lololol'),400)
        self._expect_error(GET('/p/bird'),404)

    def testPOSTErrors(self):
        self._expect_error(POST('/p/',text='that car is fast'),400)
        self._expect_error(POST('/p/',flip='this bird is far'),400)
        self._expect_error(POST('/p/',text='that mouse is black'),409)

    def testPOSTCollection(self):
        self._expect_created(POST('/p/',text='the bird flies'),'/p/bird')
        self.assertDictEqual(STORE['paragraphs']['bird'],{'text':'the bird flies'})

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
        self._expect_dict(GET('/p/*/_napix_help'),{
            'collection_methods': ['HEAD', 'GET'],
            'doc': 'Words of each paragrach',
            'managed_class': ['l', 't'],
            'resource_fields': {'word': {
                'description' : 'A word in the story',
                }},
            'resource_methods': ['HEAD', 'GET']})

    def testDocumentationError(self):
        self._expect_405(PUT('/p/*/_napix_resource_fields',
                newfields={'name':'robin'}),'HEAD,GET')


class TestConf(TestServiceBase, unittest2.TestCase):
    def setUp(self):
        self.bottle = NapixdBottle([
            Service(Paragraphs,Conf({
                'url':'para',
                'w.url':'words',
                'w.t.url':'trans'
                })) ])
        self.bottle.setup_bottle()

    def testGETCollection(self):
        self._expect_list(GET('/para/'),['/para/mouse','/para/cat'])
        self._expect_list(GET('/para/mouse/'),
                ['/para/mouse/a','/para/mouse/mouse','/para/mouse/sleeps'])
        self._expect_list(GET('/para/cat/eats/l/'),
                ['/para/cat/eats/l/e','/para/cat/eats/l/a','/para/cat/eats/l/t','/para/cat/eats/l/s'])
        self._expect_list(GET('/para/mouse/sleeps/trans/'),
                ['/para/mouse/sleeps/trans/french'])

    def testPOSTCollection(self):
        self._expect_created(POST('/para/',text='the bird flies'),
                '/para/bird')

    def testPOSTSubCollection(self):
        self._expect_created(POST('/para/cat/eats/trans/',
            language='german', translated='isst' ),
                '/para/cat/eats/trans/german')

class TestErrors(TestServiceBase, unittest2.TestCase):
    def setUp(self):
        self.bottle = NapixdBottle([ Service(Paragraphs,Conf({})) ])
        self.bottle.setup_bottle()

    def testSlash(self):
        self._expect_list(GET('/'), ['/p'])

    def testException(self):
        resp = self._expect_error(GET('/p/cat/cat/t/french'),500)
        self.assertDictEqual(resp.output,{
            'error_text' : 'I don\'t like cats',
            'error_class': 'ValueError',
            'line' : 40,
            'filename': '/home/cecedille1/enix/napix6/lib/python2.6/site-packages/napixd/test/mock/managed_class.py'
            })

if __name__ == '__main__':
    unittest2.main()
