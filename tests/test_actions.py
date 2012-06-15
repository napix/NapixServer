#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest2

from bases import TestServiceBase
from mock.managed_class import Paragraphs
from mock.request import POST,PUT,GET

from napixd.loader import NapixdBottle
from napixd.services import Service

class TestAction(TestServiceBase):
    def setUp(self):
        self.bottle = NapixdBottle([ Service(Paragraphs) ],
                no_conversation=True)
        self.bottle.setup_bottle()

    def testDiscovery(self):
        self._expect_dict(GET('/p/cat/eats/_napix_action/reverse/_napix_help'), {
            'doc': 'Reverse the word', 'mandatory': [],
            'optional': {}, 'resource_fields' : {}
            })

        self._expect_dict(GET('/p/cat/eats/_napix_action/hash/_napix_help'), {
            'doc': 'Return the word hashed with the given function',
            'mandatory': ['function'],  'optional': {},
            'resource_fields' : { 'function' : {'description' : '' , 'example' : '' } }
            })
        self._expect_dict(GET('/p/cat/eats/_napix_action/split/_napix_help'), {
            'doc': 'Extract the start from a string',
            'mandatory': ['start'],
            'optional': {'end': None},
            'resource_fields': {
                'end': {'description': '', 'example': '', 'optional': True},
                'start': {'description': '', 'example': ''}}
            })


    def testCall(self):
        self._expect_dict(POST('/p/cat/eats/_napix_action/reverse'), { 'reversed' : 'stae' })

    def testCallWithArgs(self):
        self._expect_dict(POST('/p/cat/eats/_napix_action/hash', function='md5'),
                {'hashed' : '369b4a938ff24b6c7ef69ec5149d49c5' })

    def testCallWithOptionalArgs(self):
        self._expect_dict(POST('/p/cat/eats/_napix_action/split', start='1', end='3'),
                { 'from': [1,3], 'extract' : 'at' } )
        self._expect_dict(POST('/p/cat/eats/_napix_action/split', start='1'),
                { 'from': [1,4], 'extract' : 'ats' } )

    def testSendBadInput(self):
        self._expect_error(POST('/p/cat/eats/_napix_action/hash',
            hashing='totallynotahashingfunction'), 400)
        self._expect_error(POST('/p/cat/eats/_napix_action/hash', hashing='md5'), 400)
        self._expect_error(POST('/p/cat/eats/_napix_action/hash'), 400)

        self._expect_error(POST('/p/cat/eats/_napix_action/split', start='notanactualnumber' ), 400)
        self._expect_error(POST('/p/cat/eats/_napix_action/split', start='1', end='NaN' ), 400)
        self._expect_error(POST('/p/cat/eats/_napix_action/split', end='3' ), 400)
        self._expect_error(POST('/p/cat/eats/_napix_action/split' ), 400)

    def testNotFound(self):
        self._expect_error(POST('/p/cat/do_not_exists/_napix_action/hash', function='md5'), 404)

    def testOtherVerbs(self):
        self._expect_error(PUT('/p/cat/do_not_exists/_napix_action/hash', function='md5'), 405)

if __name__ == '__main__':
    unittest2.main()
