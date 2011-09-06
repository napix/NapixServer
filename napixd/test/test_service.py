#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from napixd.test.mock.handler import MockHandler
from napixd.test.mock.request import POST,PUT,GET,DELETE
from napixd.views import Service
from bottle import HTTPError

class TestService(unittest.TestCase):
    def setUp(self):
        MockHandler.objects = {0:'foo',1:'bar'}
        self.service = Service(MockHandler)

    def testPOSTCollection(self):
        req = POST(name='mpm')
        self.service.view_collection(req)
        self.assertEqual('mpm',
                MockHandler.find(2).name)

    def testGETCollection(self):
        req = GET()
        self.assertDictEqual(
                {'values':[(0,'/mock/0'),(1,'/mock/1')]},
                self.service.view_collection(req))

    def testGETResource(self):
        req = GET()
        res = self.service.view_resource(req,1)
        self.assertEqual(res.name,'bar')
        with self.assertRaises(HTTPError):
            self.service.view_resource(req,44)

    def testPUTResource(self):
        req = PUT(name='mpm')
        self.service.view_resource(req,1)
        self.assertEqual(MockHandler.find(1).name,'mpm')
        with self.assertRaises(HTTPError):
            self.service.view_resource(req,44)

    def testDELETEResource(self):
        req = DELETE()
        self.service.view_resource(req,1)
        self.assertIsNone(MockHandler.find(1))

if __name__ == '__main__':
    unittest.main()
