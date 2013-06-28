#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.managers.base import Manager
from napixd.managers.resource_fields import ResourceFields, ResourceField, ResourceFieldsDescriptor
from napixd.exceptions import ValidationError, ImproperlyConfigured

class X(object):
    rf = ResourceFields({
        'a' : {
            'example' : u'aAaA',
            },
        'b' : {
            'example' : 123,
            'type' : int,
            'description' : 'this b is very important',
            }
        })
    def validate_resource_b(self):
        """A b should be a B or a b"""
        pass


class TestResourceFields( unittest.TestCase):
    def setUp(self):
        self.X = X
        self.x = X()

    def test_class(self):
        rf = self.X.rf
        self.assertEqual( dict(rf),  {
            'a': {
                'default_on_null': False,
                'computed': False,
                'type': 'string',
                'editable': True,
                'choices': None,
                'typing': 'static',
                'validation': '',
                'optional': False,
                'example': 'aAaA'
                },
            'b': {
                'default_on_null': False,
                'description': 'this b is very important',
                'optional': False,
                'editable': True,
                'choices': None,
                'typing': 'static',
                'validation': 'A b should be a B or a b',
                'type': 'int',
                'example': 123,
                'computed': False
                }
            }
            )

    def test_get_example(self):
        ex = self.X.rf.get_example_resource()
        self.assertEqual( ex, {
            'a': 'aAaA',
            'b': 123,
            })

    def test_descriptor(self):
        self.assertTrue( isinstance( self.x.rf, ResourceFieldsDescriptor))

class TestResourceFieldsDescriptor(unittest.TestCase):
    def setUp(self):
        self.managers = manager = mock.Mock( spec=Manager)
        self.f1 = f1 = mock.Mock( spec=ResourceField, serialize=mock.Mock(), unserialize=mock.Mock())
        f1.name = 'f1'
        f1.computed = False
        f1.type = int

        self.f2 = f2 = mock.Mock( spec=ResourceField, serialize=mock.Mock(), unserialize=mock.Mock())
        f2.name = 'f2'
        f2.computed = False
        f2.type = str

        self.rfd = ResourceFieldsDescriptor( manager, [ f1, f2 ])

    def test_serialize(self):
        r = self.rfd.serialize({
            'f1' : 1,
            'f3' : 'oh snap'
            })
        self.assertEqual( r, {
            'f1': self.f1.serialize.return_value
            })
        self.f1.serialize.assert_called_once_with( 1)

    def test_unserialize(self):
        r = self.rfd.unserialize({
            'f1' : 1,
            'f3' : 'oh snap'
            })
        self.assertEqual( r, {
            'f1': self.f1.unserialize.return_value
            })
        self.f1.unserialize.assert_called_once_with( 1)


    def test_validate(self):
        v = self.rfd.validate({
            'f1' : 1,
            'f2' : 'oh snap'
            })
        self.assertEqual( v, {
            'f1' : self.f1.validate.return_value,
            'f2' : self.f2.validate.return_value,
            })

    def test_validate_non_editable(self):
        self.f1.editable = True
        self.f2.editable = False
        v = self.rfd.validate({
            'f1' : 1,
            'f2' : 'oh snap'
            }, for_edit=True)
        self.assertEqual( v, {
            'f1' : self.f1.validate.return_value,
            })

    def test_validate_remove_computed(self):
        self.f1.computed = True
        v = self.rfd.validate({
            'f1' : 1,
            'f2' : 'oh snap'
            })
        self.assertEqual( v, {
            'f2' : self.f2.validate.return_value,
            })

    def test_validate_missing_field_required(self):
        self.f1.default_on_null = False
        self.f1.required = True

        self.assertRaises( ValidationError, self.rfd.validate, {
            'f2' : 'oh snap'
            })

    def test_validate_missing_field_optional(self):
        self.f1.default_on_null = False
        self.f1.required = False

        r = self.rfd.validate({
            'f2' : 'oh snap'
            })
        self.assertEqual( r, {
            'f2' : self.f2.validate.return_value,
            })

class TestResourceField( unittest.TestCase):
    def test_bad_type(self):
        self.assertRaises( ImproperlyConfigured, ResourceField, 'f', {
            'type':  'int'
            })

    def test_no_example_raise(self):
        self.assertRaises( ImproperlyConfigured, ResourceField, 'f', {
            })

    def test_no_example_ok(self):
        rf = ResourceField( 'f', {
            'computed' : True,
            'type': int,
            })
        self.assertEqual( rf.computed, True)
        self.assertEqual( rf.example, '')

    def test_bad_typing(self):
        self.assertRaises( ImproperlyConfigured, ResourceField, 'f', {
            'example' : 'quack',
            'typing' : 'duck',
            })

    def test_all_parameters(self):
        rf = ResourceField( 'f', {
            'type' : int,
            'example': 1,
            'optional' : True,
            'typing' : 'dynamic'
            })
        self.assertEqual( rf.type, int)
        self.assertEqual( rf.example, 1)
        self.assertEqual( rf.optional, True)
        self.assertEqual( rf.typing, 'dynamic')

    def test_check_type_dynamic(self):
        rf = ResourceField( 'f', {
            'example' : 'quack',
            'typing' : 'dynamic',
            })
        self.assertTrue( rf.check_type( 13))

    def test_check_type_static(self):
        rf = ResourceField( 'f', {
            'example' : 123,
            'type' : int
            })
        self.assertTrue( rf.check_type( 13))
        self.assertFalse( rf.check_type('mallard'))

    def test_validate_fail_check_type(self):
        rf = ResourceField( 'f', {
            'example' : 123,
            'type' : int
            })
        self.assertRaises( ValidationError, rf.validate, mock.Mock(), '123')

    def test_validate(self):
        rf = ResourceField( 'f', {
            'example' : 123,
            'type' : int,
            })
        r = rf.validate( mock.Mock( spec=object), 132 )
        self.assertEqual( r, 132)

    def test_validate_validator(self):
        rf = ResourceField( 'f', {
            'example' : 123,
            'type' : int,
            })
        vrf = mock.Mock()
        r = rf.validate( mock.Mock( spec=object, validate_resource_f=vrf), 132 )

        vrf.assert_called_once_with( 132)
        self.assertEqual( r, vrf.return_value)

    def test_choice_bad(self):
        self.assertRaises( ImproperlyConfigured, ResourceField, 'f', {
            'example' : 'mpm',
            'choices' : 123
            })

    def test_choice(self):
        rf = ResourceField( 'f', {
            'example' : 'mpm',
            'choices' : [
                'prefork',
                'worker'
                ]
            })
        rf.check_choice( 'prefork')

    def test_choice_false(self):
        rf = ResourceField( 'f', {
            'example' : 'mpm',
            'choices' : [
                'prefork',
                'worker'
                ]
            })
        self.assertRaises( ValidationError, rf.check_choice, 'patoum')

    def test_choice_callable(self):
        callable = mock.Mock( return_value=[
            'prefork',
            'worker'
            ])
        rf = ResourceField( 'f', {
            'example' : 'mpm',
            'choices' : callable
            })
        rf.check_choice( 'prefork')
        callable.assert_called_once_with()
