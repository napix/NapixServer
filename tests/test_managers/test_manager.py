#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2

from napixd.managers import Manager
from tests.mock.manager import Words,ValidationError,NotFound

class TestManager(unittest2.TestCase):
    def setUp(self):
        self.manager = Words({'words':zip(xrange(1,4),['one','two','three'])})

    def testName(self):
        self.assertEqual(self.manager.get_name(),'words')

    def testManagedClasses(self):
        self.assertListEqual(Words.get_managed_classes(),[])

    def testConfigure(self):
        self.manager.configure({'lol':'network'})

    def testExampleResource(self):
        self.assertDictEqual(self.manager.get_example_resource(),
                {'name':'four'})

    def testValidateId(self):
        self.assertRaises(ValidationError,self.manager.validate_id,'lol')
        self.assertEqual(self.manager.validate_id('1'),1)
        self.assertEqual(self.manager.validate_id('666'),666)

    def testGET(self):
        self.assertListEqual(self.manager.list_resource(),[1,2,3])
        self.assertDictEqual(self.manager.get_resource(2),
                {'name':'two','letter_count':3,'first_letter':'t'})
    def testDELETE(self):
        self.manager.delete_resource(2)
        self.assertListEqual(self.manager.list_resource(),[1,3])
        self.assertRaises(NotFound,self.manager.get_resource,2)

    def testCREATE(self):
        self.assertEqual(self.manager.create_resource({'name':'four'}),4)
        self.assertListEqual(self.manager.list_resource(),[1,2,3,4])
        self.assertDictEqual(self.manager.get_resource(4),
                {'name':'four','letter_count':4,'first_letter':'f'})
    def testPUT(self):
        self.manager.modify_resource(3,{'name':'drei'})
        self.assertDictEqual(self.manager.get_resource(3),
                {'name':'drei','letter_count':4,'first_letter':'d'})


class TestValidate( unittest2.TestCase):
    def testValidateMissingField(self):
        manager = Words()
        with self.assertRaises( ValidationError):
            manager.validate({
                'letter_count' : 1
                })

    def testValidateField(self):
        manager = Words()
        with self.assertRaises( ValidationError):
            manager.validate({
                'name' : '_napix_pouet'
                })

    def testValidateResource(self):
        manager = Words()
        cleaned = manager.validate({
            'name' : 'pouet',
            'letter_count' : 13,
            })
        self.assertDictEqual( cleaned, { 'name' : 'pouet' })

    def test_validate_noop(self):
        class TestValidateManager( Manager):
            resource_fields = { 'field1' : {} }
        vm = TestValidateManager( None)
        self.assertDictEqual( vm.validate({ 'field1' : 'abc' }), { 'field1' : 'abc' })

