#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest2
import mock

from napixd.managers.default import ReadOnlyDictManager, DictManager
from napixd.exceptions import NotFound,Duplicate


class _TestDM( unittest2.TestCase):
    def setUp(self, kls, attrs=None):
        self.parent = mock.Mock()
        self.spy_load = spy_load = mock.Mock()
        self.resources = spy_load.return_value = {
                'one':{'french':'un','german':'eins'},
                'two':{'french':'deux','german':'zwei'},
                'three':{'french':'trois','german':'drei'}
                }
        values ={
            'load' : spy_load
            }
        if attrs:
            values.update( attrs)
        Manager = type( kls)( 'RODM', ( kls, ), values)
        self.manager = Manager( self.parent)

class TestReadOnlyDict( _TestDM):
    def setUp(self):
        super( TestReadOnlyDict, self).setUp( ReadOnlyDictManager)

    def test_list_resource(self):
        self.assertSetEqual(
                set( self.manager.list_resource()),
                set( ['one','three','two'])
                )
        self.spy_load.assert_called_once_with( self.parent)

    def test_get_resource_not_exists(self):
        self.assertRaises( NotFound, self.manager.get_resource, 'four')

    def test_get_resource(self):
        self.assertDictEqual(
                self.manager.get_resource('one'),
                {'french':'un','german':'eins'})
        self.spy_load.assert_called_once_with( self.parent)

    def test_reuse(self):
        self.assertSetEqual(
                set(self.manager.list_resource()),
                set( ['one','three','two'])
                )
        self.assertDictEqual(
                self.manager.get_resource('one'),
                {'french':'un','german':'eins'})

        self.assertEqual( self.spy_load.call_count, 1)


class TestDictManager( _TestDM):
    def setUp(self):
        self.spy_save = spy_save = mock.Mock()
        self.spy_gen = spy_gen = mock.Mock()
        super( TestDictManager, self).setUp( DictManager, {
            'save': spy_save,
            'generate_new_id' : spy_gen
            })

    def test_create_resource(self):
        rd = mock.Mock()
        new_id = self.manager.create_resource( rd)
        self.spy_gen.assert_called_once_with( rd)

        self.assertEqual( new_id, self.spy_gen.return_value)

    def test_create_duplicate(self):
        rd = mock.Mock()
        self.spy_gen.return_value = 'one'
        self.assertRaises( Duplicate, self.manager.create_resource, rd)

    def test_delete_resource(self):
        self.assertRaises( NotFound, self.manager.delete_resource, 'apple')

    def test_delete_resource(self):
        self.manager.delete_resource( 'one')
        self.assertTrue( 'one' not in self.resources)

    def test_modify_resource(self):
        self.manager.modify_resource( 'one', {
            'german' : 'Kartofel'
            })
        self.assertEqual( self.resources['one']['german'], 'Kartofel')

    def test_modify_not_exists(self):
        self.assertRaises( NotFound, self.manager.modify_resource, 'potato', {
            'german' : 'Kartofel'
            })

