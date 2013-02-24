#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
from tests.mock.store_backend import MockStore

from napixd.store import Store, NoSuchStoreBackend, Counter
from napixd.store.backends.file import FileStore

class TestStore( unittest2.TestCase):
    def testImportStore(self):
        store = Store('collection', backend='FileStore')
        self.assertTrue( isinstance( store, FileStore))
        store.collection = 'collection'

    def testImportAbsoluteStore(self):
        store = Store('collection', backend='tests.mock.store_backend.MockStore')
        self.assertTrue( isinstance( store, MockStore))
        store.collection = 'collection'

    def testFailImport(self):
        self.assertRaises(NoSuchStoreBackend, Store, 'collection', backend='IDONOTEXIST')


