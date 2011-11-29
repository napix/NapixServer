#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest2
from napixd.services import Service
from napixd.test.mock.managed_class import Paragraphs
from napixd.test.mock.request import POST,PUT,GET
from napixd.conf import Conf
from napixd.loader import NapixdBottle
from napixd.test.bases import TestServiceBase

class TestAction(TestServiceBase):
    def setUp(self):
        self.bottle = NapixdBottle([ Service(Paragraphs,Conf({})) ],
                no_conversation=True)
        self.bottle.setup_bottle()

    def testDiscovery(self):
        pass

    def testCall(self):
        self._expect_dict(POST('/p/cat/eats/reverse'), { 'reversed' : 'stae' })

    def testCallWithArgs(self):
        self._expect_dict(POST('/p/cat/eats/hash', function='md5'),
                {'hashed' : '369b4a938ff24b6c7ef69ec5149d49c5' })

    def testSendBadInput(self):
        self._expect_error(POST('/p/cat/eats/hash', hashing='md5'), 400)

    def testNotFound(self):
        self._expect_error(POST('/p/cat/do_not_exists/hash', function='md5'), 404)

    def testOtherVerbs(self):
        self._expect_error(PUT('/p/cat/do_not_exists/hash', function='md5'), 405)

if __name__ == '__main__':
    unittest2.main()
