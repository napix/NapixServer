#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
from mock.store_backend import MockStore

try:
    from redis import Redis
    from napixd.store.backends import RedisStore, RedisHashStore, RedisKeyStore
except ImportError:
    Redis = False

from napixd.store.backends import FileStore, DirectoryStore
from napixd.store import Store, NoSuchStoreBackend, Counter

@unittest2.skipIf( not Redis, 'There is not Redis libs available')
class TestCounter( unittest2.TestCase):
    backend = 'RedisCounter'
    def setUp(self):
        self.counter = Counter('test', backend = self.backend)
        self.counter.reset()

    def testIncrement(self):
        self.assertEqual( self.counter.value, 0)
        self.assertEqual( self.counter.increment(), 1)
        self.assertEqual( self.counter.increment(), 2)
        self.assertEqual( self.counter.value, 2)

    def testIncrementBy(self):
        self.assertEqual( self.counter.value, 0)
        self.assertEqual( self.counter.increment(), 1)
        self.assertEqual( self.counter.increment(by=2), 3)

    def testReset(self):
        self.assertEqual( self.counter.value, 0)
        self.counter.increment()
        self.assertEqual( self.counter.reset(), 1)
        self.assertEqual( self.counter.value, 0)

class TestStore( unittest2.TestCase):
    def setUp(self):
        store  = Store('collection')
        store.drop()
        store['a'] = 'mpm'
        store  = Store('collection', backend='FileStore')
        store['b'] = 'prefork'
        store.save()

    def testStore(self):
        store = Store('collection')
        self.assertEqual( store['a'], 'mpm')
        self.assertEqual( store.get('b',False), False)

    def testImportStore(self):
        store = Store('collection', backend='FileStore')
        self.assertEqual( store['b'], 'prefork')
        self.assertEqual( store.get('a',False), False)

    def testImportAbsoluteStore(self):
        store = Store('collection', backend='tests.mock.store_backend.MockStore')
        self.assertTrue( isinstance( store, MockStore))
        store.collection = 'collection'

    def testFailImport(self):
        self.assertRaises(NoSuchStoreBackend, Store, 'collection', backend='IDONOTEXIST')

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
        self.assertEqual( len( collection), 0)
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

class TestDirectoryStore( BaseTestStore, unittest2.TestCase):
    store_class = DirectoryStore
    testNotSave = unittest2.expectedFailure( BaseTestStore.testNotSave)
    testIncrement = unittest2.expectedFailure( BaseTestStore.testIncrement)

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

