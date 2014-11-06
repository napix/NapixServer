#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest


class _BaseTestCounter(unittest.TestCase):

    def setUp(self):
        self.counter = self.counter_class('test')
        self.counter.reset()

    def test_keep_value(self):
        counter = self.counter_class('test')
        value = self.counter.increment()
        self.assertEqual(value, counter.value)

    def testIncrement(self):
        self.assertEqual(self.counter.value, 0)
        self.assertEqual(self.counter.increment(), 1)
        self.assertEqual(self.counter.increment(), 2)
        self.assertEqual(self.counter.value, 2)

    def testIncrementBy(self):
        self.assertEqual(self.counter.value, 0)
        self.assertEqual(self.counter.increment(), 1)
        self.assertEqual(self.counter.increment(by=2), 3)

    def testReset(self):
        self.assertEqual(self.counter.value, 0)
        self.counter.increment()
        self.assertEqual(self.counter.reset(), 1)
        self.assertEqual(self.counter.value, 0)


class _BaseTestStore(unittest.TestCase):

    def setUp(self):
        store = self.store_class('_napix_store_test')
        store['int'] = 1
        store['mpm'] = 'prefork'
        store.save()

    @classmethod
    def setUpClass(cls):
        cls.store_class('_napix_store_test').drop()
        cls.store_class('_napix_store_test1').drop()

    def testContains(self):
        collection = self.store_class('_napix_store_test')
        self.assertTrue('mpm' in collection)

    def testNotContains(self):
        collection = self.store_class('_napix_store_test')
        self.assertFalse('wpw' in collection)

    def testDrop(self):
        collection = self.store_class('_napix_store_test')
        collection.drop()
        self.assertEqual(len(collection), 0)
        collection = self.store_class('_napix_store_test')
        self.assertEqual(len(collection), 0)

    def testEmpty(self):
        collection = self.store_class('_napix_store_test1')
        self.assertEqual(len(collection), 0)

    def testRestoreInt(self):
        store = self.store_class('_napix_store_test')
        self.assertEqual(int(store['int']), 1)

    def testRestoreString(self):
        store = self.store_class('_napix_store_test')
        self.assertEqual(store['mpm'], 'prefork')

    def testNotSave(self):
        store = self.store_class('_napix_store_test')
        store['int'] = 2
        store = self.store_class('_napix_store_test')
        self.assertEqual(store['int'], 1)

    def testIncrement(self):
        store = self.store_class('_napix_store_test')
        self.assertEqual(store.incr('int'), 2)
        store.save()

        store = self.store_class('_napix_store_test')
        self.assertEqual(int(store['int']), 2)

    def testWrongKey(self):
        collection = self.store_class('_napix_store_test')
        self.assertRaises(KeyError, lambda: collection['nokey'])

    def testKey(self):
        collection = self.store_class('_napix_store_test')
        self.assertEqual(set(collection.keys()), set(('int', 'mpm')))
