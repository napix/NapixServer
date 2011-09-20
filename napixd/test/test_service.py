#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from napixd.test.mock.handler import Words,WordsAndLetters
from napixd.test.mock.request import POST,PUT,GET,DELETE
from napixd.services import Service
from bottle import HTTPError
from napixd.exceptions import NotFound

class TestService(unittest.TestCase):
    def setUp(self):
        self.service = Service(Words)
        self.col = self.service.collection

    def testPOSTCollection(self):
        req = POST(name='Three')
        self.service.as_collection(req)
        self.assertEqual(self.col.get(3)['name'],'Three')
    def testPOSTCollectionDuplicate(self):
        req = POST(name='Two')
        self.assertRaises(HTTPError,self.service.as_collection,req)
    def testPOSTCollectionNasty(self):
        req = POST(junk_value='lol',name='Three')
        self.service.as_collection(req)
        self.assertEqual(self.col.get(3)['name'],'Three')

    def testGETCollection(self):
        req = GET()
        self.assertEqual(sorted(self.service.as_collection(req)), [1,2])

    def testGETResource(self):
        req = GET()
        res = self.service.as_resource(req,f0=1)
        self.assertEqual(res['name'],'One')
        try:
            self.service.as_resource(req,f0=44)
        except HTTPError,e:
            self.assertTrue(isinstance(e,HTTPError))
            self.assertEqual(e.status,404)
        else:
            self.fail('Exception should have been raised')
        try:
            self.service.as_resource(req,f0='pptp')
        except HTTPError,e:
            self.assertTrue(isinstance(e,HTTPError))
            self.assertEqual(e.status,400)
        else:
            self.fail('Exception should have been raised')

    def testPUTResource(self):
        req = PUT(name='mpm')
        self.service.as_resource(req,f0=1)
        self.assertEqual(self.col.get(1)['name'],'mpm')
        self.assertRaises(HTTPError, self.service.as_resource,req,f0=44)

    def testDELETEResource(self):
        req = DELETE()
        self.service.as_resource(req,f0=1)
        self.assertRaises(NotFound,self.col.get,1)

if __name__ == '__main__':
    unittest.main()
