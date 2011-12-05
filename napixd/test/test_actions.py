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
        self._expect_dict(GET('/p/cat/eats/reverse/_napix_action'),
                {'doc': 'Reverse the word' , 'mandatory': [], 'name': 'reverse', 'optional': {}})
        self._expect_dict(GET('/p/cat/eats/hash/_napix_action'),
                {'doc': 'Return the word hashed with the given function',
                    'mandatory': ['function'], 'name': 'hash', 'optional': {}})
        self._expect_dict(GET('/p/cat/eats/split/_napix_action'),
                {'doc': 'Extract the start from a string',
                    'mandatory': ['start'], 'name': 'split', 'optional': {'end': None}})


    def testCall(self):
        self._expect_dict(POST('/p/cat/eats/reverse'), { 'reversed' : 'stae' })

    def testCallWithArgs(self):
        self._expect_dict(POST('/p/cat/eats/hash', function='md5'),
                {'hashed' : '369b4a938ff24b6c7ef69ec5149d49c5' })

    def testCallWithOptionalArgs(self):
        self._expect_dict(POST('/p/cat/eats/split', start='1', end='3'),
                { 'from': [1,3], 'extract' : 'at' } )
        self._expect_dict(POST('/p/cat/eats/split', start='1'),
                { 'from': [1,4], 'extract' : 'ats' } )

    def testSendBadInput(self):
        self._expect_error(POST('/p/cat/eats/hash', hashing='totallynotahashingfunction'), 400)
        self._expect_error(POST('/p/cat/eats/hash', hashing='md5'), 400)
        self._expect_error(POST('/p/cat/eats/hash'), 400)

        self._expect_error(POST('/p/cat/eats/split', start='notanactualnumber' ), 400)
        self._expect_error(POST('/p/cat/eats/split', start='1', end='NaN' ), 400)
        self._expect_error(POST('/p/cat/eats/split', end='3' ), 400)
        self._expect_error(POST('/p/cat/eats/split' ), 400)

    def testNotFound(self):
        self._expect_error(POST('/p/cat/do_not_exists/hash', function='md5'), 404)

    def testOtherVerbs(self):
        self._expect_error(PUT('/p/cat/do_not_exists/hash', function='md5'), 405)

if __name__ == '__main__':
    unittest2.main()
