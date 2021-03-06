#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.managers import Manager
from napixd.managers.managed_classes import ManagedClass

from napixd.conf import Conf, EmptyConf

from napixd.loader.importers import (
    Importer,
    FixedImporter,
    ConfImporter,
    RelatedImporter,
)
from napixd.loader.imports import ManagerImport
from napixd.loader.errors import ModuleImportError, ManagerImportError


class TestImporter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.package = mock.MagicMock(__file__='package.py')
        cls.patch_sys_modules = mock.patch.dict('sys.modules',
                                                package=cls.package)

    def setUp(self):
        self.importer = Importer()
        self.patch_sys_modules.start()

    def tearDown(self):
        self.patch_sys_modules.stop()

    def test_first_import_error(self):
        with mock.patch('napixd.loader.importers.import_fn',
                        side_effect=ImportError()):
            self.assertRaises(
                ModuleImportError, self.importer.import_module, 'package')

    def test_first_import_error_ignore(self):
        importer = Importer(False)
        with mock.patch('napixd.loader.importers.import_fn',
                        side_effect=ImportError()):
            self.assertRaises(
                ModuleImportError, importer.import_module, 'package')

    def test_first_import(self):
        with mock.patch('napixd.loader.importers.import_fn') as import_fn:
            mod = self.importer.first_import('package')

        import_fn.assert_called_once_with('package')
        self.assertEqual(mod, self.package)

    def test_reload(self):
        with mock.patch('__builtin__.reload') as reload_fn:
            with mock.patch('os.stat') as stat:
                stat.return_value.st_mtime = 1
                mod = self.importer.reload('package')

        reload_fn.assert_called_once_with(self.package)
        self.assertEqual(mod, self.package)

    def test_not_reload(self):
        with mock.patch('__builtin__.reload') as reload_fn:
            with mock.patch('os.stat') as stat:
                stat.return_value.st_mtime = -1
                mod = self.importer.reload('package')

        self.assertEqual(len(reload_fn.call_args_list), 0)
        self.assertEqual(mod, self.package)

    def test_reload_oserror(self):
        with mock.patch('__builtin__.reload'):
            with mock.patch('os.stat', side_effect=OSError()):
                self.assertRaises(
                    ModuleImportError, self.importer.reload, 'package')

    def test_reload_import_error(self):
        self.importer.set_timestamp(100)
        with mock.patch('__builtin__.reload', side_effect=ImportError):
            with mock.patch.object(self.importer, 'has_been_modified', return_value=True):
                self.assertRaises(ModuleImportError, self.importer.import_module, 'package')

    def test_import_reload(self):
        self.importer.set_timestamp(1000)
        with mock.patch.object(self.importer, 'reload') as meth_reload:
            mod = self.importer.import_module('package')
        self.assertEqual(mod, meth_reload.return_value)

    def test_import_import(self):
        with mock.patch.object(self.importer, 'first_import') as meth_import:
            mod = self.importer.import_module('other')
        self.assertEqual(mod, meth_import.return_value)

    def test_import_manager(self):
        with mock.patch.object(self.importer, 'import_module') as meth_import:
            mod = self.importer.import_manager('package.Manager')

        meth_import.assert_called_once_with('package')
        self.assertEqual(mod, meth_import.return_value.Manager)

    def test_import_manager_not_there(self):
        with mock.patch.object(self.importer, 'import_module', return_value=mock.Mock(spec=object())):
            self.assertRaises(ManagerImportError, self.importer.import_manager, 'package.Manager')

    def test_import_manager_not_there_reload(self):
        self.importer.set_timestamp(1000)
        with mock.patch.object(self.importer, 'import_module', return_value=mock.Mock(spec=object())):
            self.assertRaises(ManagerImportError, self.importer.import_manager, 'package.Manager')

    def test_import_manager_class(self):
        manager = type('MyManager', (Manager,), {
            '__module__': 'napixd.auto.module'
        })
        with mock.patch.object(self.importer, 'import_module') as meth_import:
            self.importer.import_manager(manager)

        meth_import.assert_called_once_with('napixd.auto.module')

    def test_import_manager_reference(self):
        with mock.patch.object(self.importer, 'import_module') as meth_import:
            reference = mock.Mock()
            self.importer.import_manager('Manager', reference=reference)

        meth_import.assert_called_once_with(reference.__module__)


class TestFixedImporter(unittest.TestCase):

    def test_importer(self):
        conf = mock.Mock(spec=Conf)
        fi = FixedImporter({
            'my': ('a.b.c.Manager', conf),
        })
        with mock.patch.object(fi, 'import_manager') as meth_import:
            managers, errors = fi.load()

        meth_import.assert_called_once_with('a.b.c.Manager')
        self.assertEqual(
            managers, [ManagerImport(meth_import.return_value, 'my', conf)])

    def test_importer_conf_convert(self):
        fi = FixedImporter({
            'my': ('a.b.c.Manager', {"a": 1}),
        })
        with mock.patch.object(fi, 'import_manager') as meth_import:
            managers, errors = fi.load()

        meth_import.assert_called_once_with('a.b.c.Manager')
        self.assertEqual(
            managers, [ManagerImport(meth_import.return_value, 'my', Conf({'a': 1}))])
        self.assertTrue(isinstance(managers[0].config, Conf))

    def test_importer_no_conf(self):
        fi = FixedImporter({
            'my': 'a.b.c.Manager',
        })
        with mock.patch.object(fi, 'import_manager') as meth_import:
            managers, errors = fi.load()

        meth_import.assert_called_once_with('a.b.c.Manager')
        self.assertEqual(
            managers, [ManagerImport(meth_import.return_value, 'my', EmptyConf())])
        self.assertTrue(isinstance(managers[0].config, EmptyConf))

    def test_importer_error(self):
        fi = FixedImporter({
            'my': 'a.b.c.Manager',
        })
        fi.set_timestamp(100)
        error = ModuleImportError('a.b.c', ImportError('Fail'))
        with mock.patch.object(fi, 'import_manager', side_effect=error):
            managers, errors = fi.load()

        self.assertEqual(managers, [])
        self.assertEqual(errors, [error])


class TestConfImporter(unittest.TestCase):
    def setUp(self):
        self.ci = ConfImporter(Conf({
            'a': 'a.b.c.Manager'
        }), Conf({
            'Manager a': {
                'd': 123
            }
        }))

    def test_importer(self):
        with mock.patch.object(self.ci, 'import_manager') as meth_import:
            managers, errors = self.ci.load()

        meth_import.assert_called_once_with('a.b.c.Manager')
        self.assertEqual(
            managers, [ManagerImport(meth_import.return_value, 'a', {'d': 123})])

    def test_importer_error(self):
        self.ci.set_timestamp(100)

        error = ManagerImportError(
            'a.b.c', 'Manager', AttributeError('No Manager in a.b.c'))
        with mock.patch.object(self.ci, 'import_manager', side_effect=error):
            managers, errors = self.ci.load()

        self.assertEqual(managers, [])
        self.assertEqual(errors, [error])


class TestRelatedImporter(unittest.TestCase):

    def setUp(self):
        ref = mock.Mock()
        self.ri = RelatedImporter(ref)

    def test_load(self):
        mc1 = mock.Mock(
            spec=ManagedClass, path='a.b.C', manager_class=mock.Mock())
        mc1.is_resolved.return_value = True
        mc2 = mock.Mock(
            spec=ManagedClass, path='a.b.B', manager_class=mock.Mock())
        mc1.is_resolved.return_value = False

        m1 = mock.Mock()
        m1.get_managed_classes.return_value = []

        with mock.patch.object(self.ri, 'import_manager') as meth_import:
            meth_import.side_effect = [m1]
            managers, errors = self.ri.load([mc1, mc2])

        mc1.resolve.assert_called_once_with(m1)
        self.assertEqual(managers, [mc1.manager_class, mc2.manager_class])

    def test_load_error(self):
        error = ManagerImportError(
            'a.b.c', 'Manager', AttributeError('No Manager in a.b.c'))
        with mock.patch.object(self.ri, 'import_manager', side_effect=error):
            managers, errors = self.ri.load([ManagedClass('a.b.C')])
        self.assertEqual(managers, [])
        self.assertEqual(errors, [error])
