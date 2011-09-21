#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from napixd.test.mock.handler import Words,WordsAndLetters
from napixd.test.mock.request import POST,PUT,GET,DELETE
from napixd.services import ServiceCollectionRequest,ServiceResourceRequest,Service


class TestServiceInternal(unittest.TestCase):
    def setUp(self):
        self.service = Service(Words)
        self.col = self.service.collection
    def testPath(self):
        args = ['one','two','three']
        kwargs = {'f0':'one','f1':'two','f2':'three'}
        for expected,real in zip(args,zip(self.service._get_path(args,{}),
                self.service._get_path(args,kwargs),
                self.service._get_path([],kwargs))):
            for x in real:
                self.assertEqual(expected,x)
    def testResourceRequest(self):
        req = GET()
        serv_req = ServiceResourceRequest(req,[1],self.col)
        self.assertTrue(serv_req.get_collection() is self.col)
        self.assertTrue(id(serv_req.get_callback(self.col)) ==  id(self.col.get))

if __name__ == '__main__':
    unittest.main()
