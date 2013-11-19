#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.managers.base import Manager
from napixd.managers.resource_fields import ResourceFields

from napixd.loader.importers import Importer
from napixd.loader.errors import ModuleImportError
from napixd.loader.imports import ManagerImport, ManagerError
from napixd.loader.loader import Loader


class TestLoader(unittest.TestCase):

    def setUp(self):
        self.importer = mock.Mock(name='Importer', spec=Importer)
        self.loader = Loader([self.importer])

        self.manager = mock.MagicMock(
            __module__='a.b',
            __name__='Manager',
            spec=Manager,
            get_managed_classes=mock.Mock(return_value=[]),
            _resource_fields=mock.MagicMock(spec=ResourceFields)
        )

    def test_load_identical(self):
        manager = mock.MagicMock(
            __module__='a.b',
            __name__='Manager',
            spec=Manager,
            get_managed_classes=mock.Mock(return_value=[]),
            _resource_fields=mock.MagicMock(spec=ResourceFields)
        )

        m1 = ManagerImport(self.manager, 'alias', {})
        m2 = ManagerImport(manager, 'alias', {})

        self.importer.load.return_value = ([m1, m2], [])
        load = self.loader.load()
        self.assertEqual(load.managers, set([m1]))
        self.assertEqual(load.old_managers, set())
        self.assertEqual(load.new_managers, set([m1]))
        self.assertEqual(load.error_managers, set())

    def test_load(self):
        m = ManagerImport(self.manager, 'alias', {})
        self.importer.load.return_value = ([m], [])
        load = self.loader.load()
        self.assertEqual(load.managers, set([m]))
        self.assertEqual(load.old_managers, set())
        self.assertEqual(load.new_managers, set([m]))
        self.assertEqual(load.error_managers, set())

    def test_load_module_error(self):
        m = ManagerImport(self.manager, 'alias', {})
        self.importer.load.return_value = ([m], [])
        self.loader.load()

        error = ImportError()
        self.importer.load.return_value = (
            [], [ModuleImportError('a.b', error)])
        load = self.loader.load()

        me = ManagerError(m.manager, 'alias', error)

        self.assertEqual(load.managers, set())
        self.assertEqual(load.old_managers, set([m]))
        self.assertEqual(load.new_managers, set())
        self.assertEqual(load.error_managers, set([me]))

    def test_load_module_error_fixed(self):
        m = ManagerImport(self.manager, 'alias', {})
        error = ImportError()
        me = ManagerError(m.manager, 'alias', error)

        self.importer.load.return_value = ([m], [])
        self.loader.load()

        self.importer.load.return_value = (
            [], [ModuleImportError('a.b', error)])
        self.loader.load()

        self.importer.load.return_value = ([m], [])
        load = self.loader.load()

        self.assertEqual(load.managers, set([m]))
        self.assertEqual(load.old_managers, set([me]))
        self.assertEqual(load.new_managers, set([m]))
        self.assertEqual(load.error_managers, set([]))

    def test_load_module_error_new_error(self):
        m = ManagerImport(self.manager, 'alias', {})
        self.importer.load.return_value = ([m], [])
        self.loader.load()

        error = ImportError('First Error')
        self.importer.load.return_value = (
            [], [ModuleImportError('a.b', error)])
        load = self.loader.load()

        new_error = ImportError('New Error')
        self.importer.load.return_value = (
            [], [ModuleImportError('a.b', new_error)])
        load = self.loader.load()

        me = ManagerError(m.manager, 'alias', new_error)

        self.assertEqual(load.managers, set())
        self.assertEqual(load.old_managers, set())
        self.assertEqual(load.new_managers, set())
        self.assertEqual(load.error_managers, set([me]))
