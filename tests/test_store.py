#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest2
import os
import shutil
try:
    from redis import Redis
    from napixd.store import RedisStore, RedisHashStore, RedisKeyStore
except ImportError:
    Redis = False

from napixd.store import FileStore

class BaseTestStore(object):
    def setUp( self):
        store = self.store_class( '_napix_store_test')
        store['int'] = 1
        store['mpm'] = 'prefork'
        store.save()

    @classmethod
    def setUpClass( cls):
        cls.store_class('_napix_store_test').drop()
        cls.store_class('_napix_store_test1').drop()

    def testDrop( self):
        collection = self.store_class( '_napix_store_test')
        collection.drop()
        collection = self.store_class( '_napix_store_test')
        self.assertEqual( len( collection), 0)

    def testEmpty(self):
        collection = self.store_class( '_napix_store_test1')
        self.assertEqual( len( collection), 0)

    def testRestoreInt(self):
        store = self.store_class( '_napix_store_test')
        self.assertEqual(int( store['int']), 1)

    def testRestoreString(self):
        store = self.store_class( '_napix_store_test')
        self.assertEqual(store['mpm'], 'prefork')

    def testNotSave(self):
        store = self.store_class( '_napix_store_test')
        store['int'] = 2
        store = self.store_class( '_napix_store_test')
        self.assertEqual(store['int'], 1)

    def testIncrement( self):
        store = self.store_class( '_napix_store_test')
        self.assertEqual(store.incr('int'), 2)
        store.save()

        store = self.store_class( '_napix_store_test')
        self.assertEqual(int(store['int']), 2)

    def testWrongKey( self):
        collection = self.store_class( '_napix_store_test')
        self.assertRaises( KeyError, lambda :collection['nokey'])

    def testKey(self):
        collection = self.store_class( '_napix_store_test')
        self.assertEqual( set(collection.keys()), set( ('int', 'mpm' ) ))

class TestFileStore( BaseTestStore, unittest2.TestCase):
    store_class = FileStore
    def testCreateDirectory(self):
        collection = self.store_class( '_napix_store_test', '/tmp/_napix_store/test_dir')
        self.assertEqual( len( collection), 0)
        collection.save()

@unittest2.skipIf( not Redis, 'There is not Redis libs available')
class TestRedisStore(BaseTestStore, unittest2.TestCase):
    store_class = RedisStore

@unittest2.skipIf( not Redis, 'There is not Redis libs available')
class TestRedisHashStore(BaseTestStore, unittest2.TestCase):
    store_class = RedisHashStore
    testNotSave = unittest2.expectedFailure( BaseTestStore.testNotSave)

@unittest2.skipIf( not Redis, 'There is not Redis libs available')
class TestRedisKeyStore(BaseTestStore, unittest2.TestCase):
    store_class = RedisKeyStore
    testNotSave = unittest2.expectedFailure( BaseTestStore.testNotSave)

if __name__ == '__main__':
    unittest2.main()
