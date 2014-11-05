#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest

from napixd.store import Store, NoSuchStoreBackend, Loader
from napixd.store.backends.file import FileStore
from napixd.conf import Conf

from tests.test_store.store_backend import MockBackend


class TestStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conf = Conf({
            'store': 'tests.test_store.store_backend.MockBackend',
            'Store tests.test_store.store_backend.MockBackend': {
                'this': 'that'
            }
        })

    def setUp(self):
        Loader._instance = Loader(self.conf)
        MockBackend.set_options.reset_mock()

    @classmethod
    def tearDownClass(self):
        Conf.set_default(None)

    def test_default_store(self):
        store = Store('collection')
        MockBackend.set_options.assert_called_once_with({'this': 'that'})
        self.assertEqual(store, MockBackend.return_value.return_value)

    def testImportStore(self):
        store = Store(
            'collection', backend='napixd.store.backends.file.FileBackend')
        self.assertTrue(isinstance(store, FileStore))

    def testImportAbsoluteStore(self):
        store = Store('collection',
                      backend='tests.test_store.store_backend.MockBackend')
        self.assertEqual(store, MockBackend.return_value.return_value)

    def testFailImport(self):
        self.assertRaises(
            NoSuchStoreBackend, Store, 'collection', backend='IDONOTEXIST')
        self.assertRaises(
            NoSuchStoreBackend, Store, 'collection', backend='I.DO.NOT.EXIST')
