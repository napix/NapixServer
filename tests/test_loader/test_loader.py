#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.managers.base import Manager
from napixd.managers.resource_fields import ResourceFields
from napixd.managers.managed_classes import ManagedClass

from napixd.loader.importers import Importer
from napixd.loader.errors import ModuleImportError, ManagerImportError
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

    def test_setup(self):
        self.manager.get_managed_classes.return_value = ['a.b.C']

        manager_class = mock.Mock(name='managed')
        related_manager = mock.Mock(
            name='related',
            spec=ManagedClass,
            manager_class=manager_class
        )
        manager_class.get_managed_classes.return_value = []
        related_manager.is_resolved.return_value = False
        with mock.patch('napixd.loader.loader.RelatedImporter') as Importer:
            importer = Importer.return_value
            importer.load.return_value = ([manager_class], [])
            self.loader.setup(self.manager)

        Importer.assert_called_once_with(self.manager)
        importer.load.assert_called_once_with(['a.b.C'])

    def test_setup_error(self):
        m = ManagerImport(self.manager, 'alias', {})
        self.importer.load.return_value = ([m], [])
        self.manager.get_managed_classes.return_value = ['a.b.C']

        error = ModuleImportError('a.b', ImportError())
        with mock.patch('napixd.loader.loader.RelatedImporter') as Importer:
            importer = Importer.return_value
            importer.load.side_effect = error
            load = self.loader.load()

        Importer.assert_called_once_with(self.manager)
        importer.load.assert_called_once_with(['a.b.C'])

        me = ManagerError(m.manager, 'alias', error)
        self.assertEqual(load.error_managers, set([me]))

    def test_setup_circular(self):
        self.manager.get_managed_classes.return_value = [self.manager]

        with mock.patch('napixd.loader.loader.RelatedImporter') as Importer:
            importer = Importer.return_value
            importer.load.return_value = ([self.manager], [])
            self.loader.setup(self.manager)

        Importer.assert_called_once_with(self.manager)

    def test_setup_resource_fields(self):
        self.manager._resource_fields.__nonzero__.return_value = False
        self.assertRaises(ManagerImportError, self.loader.setup, self.manager)

    def test_setup_resource_fields_submanager(self):
        self.manager.get_managed_classes.return_value = ['a.b.C']

        manager_class = mock.MagicMock(name='managed')
        manager_class._resource_fields.__nonzero__.return_value = False
        related_manager = mock.Mock(
            name='related',
            spec=ManagedClass,
            manager_class=manager_class
        )
        related_manager.is_resolved.return_value = False

        with mock.patch('napixd.loader.loader.RelatedImporter') as Importer:
            importer = Importer.return_value
            importer.load.return_value = ([manager_class], [])
            self.assertRaises(ManagerImportError, self.loader.setup, self.manager)
