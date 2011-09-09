#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.queue import ThrowingSubQueue,ThrowingQueue,SubQueue,Queue,Empty
import unittest
from time import time

class TestQueue(unittest.TestCase):
    def setUp(self):
        self.main_queue = Queue()
        self.throwing_queue = ThrowingQueue()
        self.sub_queue1 = SubQueue(self.main_queue)
        self.sub_queue2 = SubQueue(self.main_queue)
        self.throwing_sub_queue = ThrowingSubQueue(self.main_queue)

    def testTimeOut(self):
        start=time()
        self.assertRaises(Empty,
            self.main_queue.get,timeout=1)
        self.assertAlmostEquals(start+1,time(),places=3)

    def testEmpty(self):
        self.assertRaises(Empty,self.sub_queue1.get,False)
        self.assertRaises(Empty,self.main_queue.get,False)
        self.assertRaises(Empty,self.throwing_queue.get,False)
        self.assertRaises(Empty,self.throwing_sub_queue.get,False)

    def testMainQueue(self):
        self.main_queue.put('x')
        self.assertEqual(self.main_queue.get(),'x')

    def testThrowing(self):
        self.throwing_queue.put(Exception('mpm'))
        self.assertRaises(Exception,
            self.throwing_queue.get)

    def testSubQueue(self):
        self.sub_queue1.put('x')
        self.sub_queue2.put('y')
        self.assertEqual(self.sub_queue1.get('x'),'x')
        self.assertEqual(self.main_queue.get('x'),'x')
        self.assertEqual(self.main_queue.get('y'),'y')
        self.assertEqual(self.sub_queue2.get('y'),'y')

    def testThrowingSubQueue(self):
        self.throwing_sub_queue.put(Exception('mpm'))
        self.assertRaises(Exception,
            self.throwing_sub_queue.get)
        value = self.main_queue.get()
        self.assertTrue(isinstance(value,Exception))
        self.assertEqual(str(value),'mpm')

if __name__ == '__main__':
    unittest.main()
