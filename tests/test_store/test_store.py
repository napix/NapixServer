#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest

from napixd.store import Store, NoSuchStoreBackend
from napixd.store.backends.file import FileStore
from tests.mock.store_backend import MockBackend


class TestStore(unittest.TestCase):

    def testImportStore(self):
        store = Store(
            'collection', backend='napixd.store.backends.file.FileBackend')
        self.assertTrue(isinstance(store, FileStore))
        store.collection = 'collection'

    def testImportAbsoluteStore(self):
        store = Store('collection',
                      backend='tests.mock.store_backend.MockBackend')
        self.assertEqual(store, MockBackend.return_value.return_value)
        store.collection = 'collection'

    def testFailImport(self):
        self.assertRaises(
            NoSuchStoreBackend, Store, 'collection', backend='IDONOTEXIST')
        self.assertRaises(
            NoSuchStoreBackend, Store, 'collection', backend='I.DO.NOT.EXIST')
