#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from napixd.test.mock.handler import Words,WordsAndLetters,LettersOfWord
from napixd.exceptions import ValidationError,NotFound,Duplicate


class _TestWords:
    def setUp(self):
        self.handler = self.klass({ 0:'lol',1:'foo',2:'bar',3:'baz'})
    def testID(self):
        self.assertEqual(self.handler.check_id('1'),1)
        self.assertEqual(self.handler.check_id('2'),2)
        self.assertRaises(ValidationError,self.handler.check_id,'mpm')
    def testFind(self):
        self.assertRaises(NotFound,self.handler.get,9)
        result = self.handler.get(0)
        self.assertEqual(result['name'],'lol')
        self.assertEqual(len(result),1)
    def testFindAll(self):
        self.assertEqual(sorted(self.handler.list()),[0,1,2,3])
        self.assertEqual(sorted(self.handler.list({'max':2})),[0,1,2])
    def testCreate(self):
        new_id = self.handler.create({'name':'mpm'})
        self.assertEqual(new_id,4)
        result = self.handler.get(4)
        self.assertEqual(result['name'],'mpm')
    def testDelete(self):
        self.handler.delete(3)
        self.assertRaises(NotFound,self.handler.get,3)
    def testModify(self):
        self.handler.modify(2,{'name':'mpm'})
        self.assertEqual(self.handler.get(2)['name'],'mpm')

class TestWords(_TestWords,unittest.TestCase):
    klass=Words

class TestWordsAndLettes(_TestWords,unittest.TestCase):
    klass=WordsAndLetters
    def setUp(self):
        super(TestWordsAndLettes,self).setUp()
        self.resource = self.handler.child(0)

    def testSubResource(self):
        self.assertEqual(self.resource['name'],'lol')

    def testSubList(self):
        self.assertEqual(sorted(self.resource.letters.list()),['l','o'])

    def testDefaultCheckID(self):
        self.assertRaises(ValidationError,self.resource.letters.check_id,'')

    def testSubInstance(self):
        o_in_lol = self.resource.letters.get('o')
        self.assertEqual(o_in_lol['count'],1)
        self.assertEqual(o_in_lol['ord'],111)
        l_in_lol = self.resource.letters.get('l')
        self.assertEqual(l_in_lol['count'],2)

    def testCollection(self):
        self.assertEqual(
                self.handler.resource_class._subresources[0],'letters')
        self.assertEqual(
                self.handler.resource_class.letters,LettersOfWord)

if __name__ == '__main__':
    unittest.main()
