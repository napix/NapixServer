#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest2
import os
import shutil
try:
    from redis import Redis
except ImportError:
    Redis = False

from napixd.store import FileStore, RedisStore

class BaseTestStore(object):
    def setUp( self):
        store = self.store_class( '_napix_store_test')
        store['value'] = 1
        store.save()
    def testEmpty(self):
        collection = self.store_class( '_napix_store_test1')
        self.assertEqual( len( collection), 0)

    def testRestore(self):
        store = self.store_class( '_napix_store_test')
        self.assertEqual(store['value'], 1)

    def testNotSave(self):
        store = self.store_class( '_napix_store_test')
        store['value'] = 2
        store = self.store_class( '_napix_store_test')
        self.assertEqual(store['value'], 1)

class TestFileStore( BaseTestStore, unittest2.TestCase):
    store_class = FileStore
    @classmethod
    def setUpClass( cls):
        if os.path.isfile( '/tmp/_napix_store_test1'):
            os.unlink( '/tmp/_napix_store_test1')
        if os.path.isdir( '/tmp/_napix_store/test_dir'):
            shutil.rmtree( '/tmp/_napix_store/test_dir')
    def testCreateDirectory(self):
        collection = self.store_class( '_napix_store_test', '/tmp/_napix_store/test_dir')
        self.assertEqual( len( collection), 0)
        collection.save()

unittest2.skipIf( not Redis, 'There is not Redis libs available')
class TestRedisStore( BaseTestStore, unittest2.TestCase):
    store_class = RedisStore
    @classmethod
    def setUpClass( cls):
        redis = Redis()
        redis.delete( '_napix_store_test1', None)

if __name__ == '__main__':
    unittest2.main()
