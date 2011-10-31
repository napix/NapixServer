#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
from napixd.test.mock.managed_class import Paragraphs,STORE
from napixd.test.mock.request import POST,PUT,GET,DELETE
from napixd.conf import Conf
from napixd.services import Service
import bottle

class TestServiceBase(object):
    def _do_the_request(self,request):
        bottle.request = request
        app,args = self.bottle.match(request.environ)
        return app(**args)
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
        else:
            self.fail('Unexpected %s'%repr(resp))
    def _expect_redirect(self,request,url):
        try:
            resp = self._do_the_request(request)
        except bottle.HTTPResponse,e:
            self.assertEqual(e.status, 303)
            self.assertEqual(e.headers['Location'],url)
        else:
            self.fail('Unexpected %s'%repr(resp))

class TestService(TestServiceBase, unittest2.TestCase):
    def setUp(self):
        self.bottle = bottle.Bottle(autojson=False)
        self.service = Service(Paragraphs,Conf({}))
        self.service.setup_bottle(self.bottle)

    def testGETCollection(self):
        self._expect_list(GET('/p/'),['mouse','cat'])
        self._expect_list(GET('/p/mouse/'),['a','mouse','sleeps'])
        self._expect_list(GET('/p/cat/eats/l/'),['e','a','t','s'])
        self._expect_list(GET('/p/mouse/sleeps/t/'),['french'])

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
        self._expect_redirect(POST('/p/',text='the bird flies'),'/p/bird')
        self.assertDictEqual(STORE['paragraphs']['bird'],{'text':'the bird flies'})

    def testPOSTSubCollection(self):
        self._expect_redirect(POST('/p/cat/eats/t/', language='german', translated='isst' ),
                '/p/cat/eats/t/german')
        self.assertDictEqual(STORE['translations'], {
                    'french':{ 'translated':'mange', 'language':'french'},
                    'german':{  'translated':'isst', 'language':'german'}
                    })

    def testPUTResource(self):
        PUT('/p/mouse',text='the mouse is close')

    def testDELETEResource(self):
        DELETE('/p/mouse')


class TestConf(TestServiceBase, unittest2.TestCase):
    def setUp(self):
        self.bottle = bottle.Bottle(autojson=False)
        self.service = Service(Paragraphs,Conf({
            'url':'para',
            'w.url':'words',
            'w.t.url':'trans'
            }))
        self.service.setup_bottle(self.bottle)

    def testGETCollection(self):
        self._expect_list(GET('/para/'),['mouse','cat'])
        self._expect_list(GET('/para/mouse/'),['a','mouse','sleeps'])
        self._expect_list(GET('/para/cat/eats/l/'),['e','a','t','s'])
        self._expect_list(GET('/para/mouse/sleeps/trans/'),['french'])

    def testPOSTCollection(self):
        self._expect_redirect(POST('/para/',text='the bird flies'),'/para/bird')

    def testPOSTSubCollection(self):
        self._expect_redirect(POST('/p/cat/eats/t/', language='german', translated='isst' ),
                '/para/cat/eats/trans/german')

if __name__ == '__main__':
    unittest2.main()
