#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest

from napixd.store import Store, NoSuchStoreBackend
from napixd.store.backends.file import FileStore
from napixd.conf import Conf

from tests.mock.store_backend import MockBackend


class TestStore(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        Conf.set_default(Conf({
            'Napix.storage': {
                'store': 'tests.mock.store_backend.MockBackend'
            }
        }))

    @classmethod
    def tearDownClass(self):
        Conf.set_default(None)

    def test_default_store(self):
        store = Store('collection')
        self.assertEqual(store, MockBackend.return_value.return_value)

    def testImportStore(self):
        store = Store(
            'collection', backend='napixd.store.backends.file.FileBackend')
        self.assertTrue(isinstance(store, FileStore))

    def testImportAbsoluteStore(self):
        store = Store('collection',
                      backend='tests.mock.store_backend.MockBackend')
        self.assertEqual(store, MockBackend.return_value.return_value)

    def testFailImport(self):
        self.assertRaises(
            NoSuchStoreBackend, Store, 'collection', backend='IDONOTEXIST')
        self.assertRaises(
            NoSuchStoreBackend, Store, 'collection', backend='I.DO.NOT.EXIST')
