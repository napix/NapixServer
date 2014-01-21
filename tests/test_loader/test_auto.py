#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import

import unittest
import mock

from napixd.managers import Manager
from napixd.conf import EmptyConf
from napixd.loader.imports import ManagerImport
from napixd.loader.errors import ModuleImportError

from napixd.loader.auto import AutoImporter


class TestAutoImporter(unittest.TestCase):

    def setUp(self):
        with mock.patch('sys.path'):
            self.ai = AutoImporter('/a/b')

    def test_get_paths(self):
        self.assertEqual(self.ai.get_paths(), ['/a/b'])

    def test_import_module_error(self):
        with mock.patch('napixd.loader.auto.imp') as pimp:
            pimp.load_module.side_effect = SyntaxError()

            with mock.patch('__builtin__.open') as Open:
                open = Open.return_value
                open.__enter__.return_value = open
                self.assertRaises(
                    ModuleImportError, self.ai.import_module, 'b.py')

    def test_import_module(self):
        with mock.patch('napixd.loader.auto.imp') as pimp:
            with mock.patch('__builtin__.open') as Open:
                with mock.patch.object(self.ai, 'has_been_modified', return_value=True):
                    open = Open.return_value
                    open.__enter__.return_value = open
                    self.ai.import_module('b.py')

        pimp.load_module.assert_called_once_with(
            'napixd.auto.b',
            open,
            '/a/b/b.py',
            ('py', 'U', pimp.PY_SOURCE)
        )

    def test_auto_importer(self):
        module = mock.MagicMock(
            spec=object(),
            __all__=('A', 'B', 'C'),
            __name__ = 'napixd.auto.module',
            A=object(),
            B=type('Manager', (Manager, ), {
                '__module__': 'napixd.auto.module',
                'resource_fields': {
                    's': {'example': 1}
                },
                'name': 'my_manager',
                'configure': mock.MagicMock(__doc__='{ "a" : 1 }')
            }),
        )
        with mock.patch('os.listdir', return_value=['b.pyc', 'b.py', '.b.swp']):
            with mock.patch.object(self.ai, 'import_module', return_value=module) as meth_import:
                modules, errors = self.ai.load()

        meth_import.assert_called_once_with('b.py')
        self.assertEqual(
            modules, [ManagerImport(module.B, 'my_manager', {'a': 1})])
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(error.module, 'napixd.auto.module')

    def test_auto_importer_mod_error(self):
        error = ModuleImportError('b', ImportError())
        with mock.patch('os.listdir', return_value=['b.py']):
            with mock.patch.object(self.ai, 'import_module', side_effect=error):
                modules, errors = self.ai.load()

        self.assertEqual(errors, [error])

    def test_auto_importer_no_detect(self):
        module = mock.MagicMock(
            __name__='napixd.auto.module',
            spec=object(),
            B=type('Manager', (Manager, ), {
                'detect': mock.Mock(return_value=False)}),
        )
        with mock.patch('os.listdir', return_value=['b.py']):
            with mock.patch.object(self.ai, 'import_module', return_value=module):
                modules, errors = self.ai.load()

        self.assertEqual(modules, [])
        self.assertEqual(errors, [])

    def test_auto_importer_detect_error(self):
        module = mock.MagicMock(
            __name__='napixd.auto.module',
            spec=object(),
            B=type('Manager', (Manager, ), {
                'detect': mock.Mock(side_effect=ValueError('oops'))}),
        )
        with mock.patch('os.listdir', return_value=['b.py']):
            with mock.patch.object(self.ai, 'import_module', return_value=module):
                modules, errors = self.ai.load()

        self.assertEqual(modules, [])
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(error.module, 'napixd.auto.module')
        self.assertEqual(error.manager, 'B')
        self.assertTrue(isinstance(error.cause, ValueError))

    def test_get_config_from(self):
        mgr = type('Manager', (Manager, ), {
            'name': 'my_manager',
            'configure': mock.MagicMock(__doc__='{ "a : 1 }')
        })

        conf = self.ai.get_config_from(mgr)
        self.assertTrue(isinstance(conf, EmptyConf))
