#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from napixd.test.mock.handler import MockHandler,MockHandlerWithAction
from napixd.exceptions import ValidationError
from napixd.base import check_handler,HandlerDefinitionError


class TestHandler(unittest.TestCase):
    def setUp(self):
        MockHandler.objects = { 0:'lol',1:'foo',2:'bar',3:'baz'}
    def testID(self):
        self.assertEqual(MockHandler.validate_resource_id('0'),0)
        self.assertEqual(MockHandler.validate_resource_id('2'),2)
        self.assertRaises(ValidationError,MockHandler.validate_resource_id,'mpm')
    def testFind(self):
        self.assertIsNone(MockHandler.find(9))
        result = MockHandler.find(0)
        self.assertEqual(result.rid,0)
        self.assertEqual(result.name,'lol')
        self.assertDictEqual({'rid':0,'name':'lol'},result.serialize())
    def testFindAll(self):
        self.assertEqual(sorted(MockHandler.find_all()),[0,1,2,3])
    def testCreate(self):
        self.assertEqual(MockHandler.create({'name':'mpm'}),4)
        self.assertIsNotNone(MockHandler.find(4))
    def testDelete(self):
        MockHandler.find(3).remove()
        self.assertIsNone(MockHandler.find(3))
    def testModify(self):
        res = MockHandler.find(2)
        res.modify({'name':'mpm'})
        self.assertEqual(MockHandler.find(2).name,'mpm')
    def testMeta(self):
        try:
            check_handler(MockHandler)
        except HandlerDefinitionError:
            self.fail('Should not have been here')

class TestHandlerWithAction(unittest.TestCase):
    def setUp(self):
        MockHandlerWithAction.objects = {1:'mpm'}
    def testActionParams(self):
        self.assertListEqual(MockHandlerWithAction.without_args.mandatory,[])
        self.assertDictEqual(MockHandlerWithAction.without_args.optional,{})
        self.assertDictEqual(MockHandlerWithAction.with_args.optional,{'opt1':None,'opt2':None})
        self.assertListEqual(MockHandlerWithAction.with_args.mandatory,['mand'])

    def testWithOut(self):
        res = MockHandlerWithAction.find(1)
        self.assertEqual(res.without_args(),909)
        self.assertRaises(ValueError,res.without_args,dude=1)
    def testWith(self):
        res = MockHandlerWithAction.find(1)
        self.assertDictEqual(
                {'mand':'lol','opt1':'mpm','opt2':'prefork'},
                res.with_args(mand='lol',opt1='mpm',opt2='prefork'))
        self.assertDictEqual(
                {'mand':'lol','opt1':None,'opt2':None},
                res.with_args(mand='lol'))
        self.assertRaises(TypeError,res.with_args,dude=1,mand=True)
        self.assertRaises(TypeError,res.with_args,opt1=1,opt2=2)

if __name__ == '__main__':
    unittest.main()
