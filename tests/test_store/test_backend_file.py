#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os

from napixd.store.backends import file
from tests.test_store.base import _BaseTestStore


class TestFileStore(_BaseTestStore):
    store_class = file.FileBackend({})

    @classmethod
    def setUpClass(cls):
        if os.path.isdir('/tmp/_napix_store_test/test_dir'):
            os.rmdir('/tmp/_napix_store_test/test_dir')

    def testCreateDirectory(self):
        backend = file.FileBackend({'root': '/tmp/_napix_store/test_dir'})
        collection = backend('_napix_store_test')
        self.assertEqual(len(collection), 0)
        collection.save()


class TestDirectoryStore(_BaseTestStore):
    store_class = file.DirectoryBackend({})
    testNotSave = unittest.expectedFailure(_BaseTestStore.testNotSave)
    testIncrement = unittest.expectedFailure(_BaseTestStore.testIncrement)
