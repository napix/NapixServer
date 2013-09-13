#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest2
import mock

from napixd.managers.default import ReadOnlyDictManager, DictManager, FileManager
from napixd.exceptions import NotFound, Duplicate
from napixd.services.wrapper import Wrapper


class _TestDM(unittest2.TestCase):

    def setUp(self, kls, attrs=None):
        self.parent = mock.Mock()
        self.spy_load = spy_load = mock.Mock()
        self.resources = spy_load.return_value = {
            'one': {'french': 'un', 'german': 'eins'},
            'two': {'french': 'deux', 'german': 'zwei'},
            'three': {'french': 'trois', 'german': 'drei'}
        }
        values = {
            'load': spy_load
        }
        if attrs:
            values.update(attrs)
        Manager = type(kls)('RODM', (kls, ), values)
        self.manager = Manager(self.parent)


class TestReadOnlyDict(_TestDM):

    def setUp(self):
        super(TestReadOnlyDict, self).setUp(ReadOnlyDictManager)

    def test_list_resource(self):
        self.assertSetEqual(
            set(self.manager.list_resource()),
            set(['one', 'three', 'two'])
        )
        self.spy_load.assert_called_once_with(self.parent)

    def test_return_not_dict(self):
        self.spy_load.return_value = None
        self.assertRaises(ValueError, self.manager.list_resource)

    def test_get_resource_not_exists(self):
        self.assertRaises(NotFound, self.manager.get_resource, 'four')

    def test_get_resource(self):
        self.assertDictEqual(
            self.manager.get_resource('one'),
            {'french': 'un', 'german': 'eins'})
        self.spy_load.assert_called_once_with(self.parent)

    def test_reuse(self):
        self.assertSetEqual(
            set(self.manager.list_resource()),
            set(['one', 'three', 'two'])
        )
        self.assertDictEqual(
            self.manager.get_resource('one'),
            {'french': 'un', 'german': 'eins'})

        self.assertEqual(self.spy_load.call_count, 1)


class TestDictManager(_TestDM):

    def setUp(self):
        self.spy_save = spy_save = mock.Mock()
        self.spy_gen = spy_gen = mock.Mock()
        super(TestDictManager, self).setUp(DictManager, {
            'save': spy_save,
            'generate_new_id': spy_gen
        })

    def test_create_resource(self):
        rd = mock.Mock()
        new_id = self.manager.create_resource(rd)
        self.spy_gen.assert_called_once_with(rd)

        self.assertEqual(new_id, self.spy_gen.return_value)

    def test_create_duplicate(self):
        rd = mock.Mock()
        self.spy_gen.return_value = 'one'
        self.assertRaises(Duplicate, self.manager.create_resource, rd)

    def test_delete_resource_not_found(self):
        self.assertRaises(NotFound, self.manager.delete_resource,
                          Wrapper(self.manager, 'apple'))

    def test_delete_resource(self):
        self.manager.delete_resource(Wrapper(self.manager, 'one'))
        self.assertTrue('one' not in self.manager.resources)

    def test_modify_resource(self):
        self.manager.modify_resource(
            Wrapper(self.manager, 'one', self.resources['one']), {
                'german': 'Kartofel'
            })
        self.assertEqual(self.resources['one']['german'], 'Kartofel')

    def test_modify_not_exists(self):
        self.assertRaises(NotFound, self.manager.modify_resource,
                          Wrapper(self.manager, 'potato'), {
                              'german': 'Kartofel'
                          })


class MyFileManager(FileManager):

    def get_filename(self, context):
        return context.fname

    def write(self, fp, resources):
        self.context.write(fp, resources)

    def parse(self, fp):
        self.context.parse(fp)
        return {'a': 1}


class TestFileManager(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        open_side_effect = lambda x, y: open(
            x, y) if isinstance(x, basestring) else mock.DEFAULT
        cls.patch_open = mock.patch(
            '__builtin__.open', side_effect=open_side_effect)

    def setUp(self):
        self.parent = mock.Mock()
        self.fm = MyFileManager(self.parent)

    def test_is_up_to_date_first(self):
        self.assertFalse(self.fm.is_up_to_date())

    def test_is_up_to_date(self):
        with mock.patch('napixd.managers.default.time', return_value=2):
            with self.patch_open:
                self.fm.load(self.parent)
        with mock.patch('os.path.getmtime', return_value=1):
            self.assertTrue(self.fm.is_up_to_date())

    def test_save(self):
        resources = mock.Mock()

        with self.patch_open as popen:
            popen.return_value.__enter__.return_value = popen.return_value
            self.fm.save(self.parent, resources)

        popen.assert_called_once_with(self.parent.fname, 'w')
        self.parent.write.assert_called_once_with(
            popen.return_value, resources)

    def test_load(self):
        with self.patch_open as popen:
            popen.return_value.__enter__.return_value = popen.return_value
            self.fm.load(self.parent)

        popen.assert_called_once_with(self.parent.fname, 'r')
        self.parent.parse.assert_called_once_with(popen.return_value)

    def test_load_error(self):
        with self.patch_open as popen:
            popen.side_effect = IOError()
            self.assertEqual(self.fm.resources, {})
