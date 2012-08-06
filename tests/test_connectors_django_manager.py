#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
import os
import shutil

from napixd.managers import Manager
from napixd.exceptions import NotFound

from napixd.connectors.django import ( DjangoImport,
        DjangoReadOperations, DjangoWriteOperations,
        DjangoRelatedModelManager, DjangoModelManager)

with DjangoImport( 'tests.mock.django_settings'):
    import mock.django_models as models
    from django.conf import settings

def tearDownModule():
    os.unlink( settings.DATABASES['default']['NAME'])

class ROManager( DjangoReadOperations, Manager):
    model = models.Car
    resource_fields = {
            'name' : {},
            'owner' : {},
            'max_speed' : {},
            'created' : { 'computed' : True}
            }
    def get_queryset(self):
        return self.model.objects.all()

class TestReadOperation(unittest2.TestCase):
    @classmethod
    def setUpClass( cls):
        db = settings.DATABASES['default']['NAME']
        shutil.copy( db+'.master', db)

    def test_get(self):
        rom = ROManager(None)
        self.assertTrue( rom.get_resource(1))

    def test_get_not_found(self):
        rom = ROManager(None)
        self.assertRaises( NotFound, rom.get_resource, 10)

    def test_list(self):
        rom = ROManager(None)
        self.assertEqual( sorted( rom.list_resource()), [ 1, 2, 3])

class WManager( DjangoWriteOperations, Manager):
    model = models.Car
    resource_fields = {
            'name' : {},
            'owner' : {},
            'max_speed' : {},
            'created' : { 'computed' : True}
            }
    def get_queryset(self):
        return self.model.objects.all()

class TestWriteOperation( unittest2.TestCase):
    def setUp( cls):
        db = settings.DATABASES['default']['NAME']
        shutil.copy( db+'.master', db)

    def test_delete( self):
        wm = WManager(None)
        wm.delete_resource(1)
        self.assertRaises( NotFound, wm.delete_resource, 1)
        self.assertEqual( models.Car.objects.filter( id=1).count(), 0)

    def test_create(self):
        wm = WManager(None)
        new_id = wm.create_resource({
            'name' : 'jaguar',
            'owner' : '',
            'max_speed': 200
            })
        self.assertEqual( new_id, 4)
        jag = models.Car.objects.get( id = 4)
        self.assertEqual( jag.name, 'jaguar')

    def test_modify( self):
        wm = WManager(None)
        wm.modify_resource(1, {
            'name' : 'targa4s',
            'owner' : '',
            'max_speed': 20
            })
        jag = models.Car.objects.get( id = 1)
        self.assertEqual( jag.name, 'targa4s')
        self.assertEqual( jag.max_speed, 20)


class TestResourceFieldGeneration(unittest2.TestCase):
    def _make_class(self,**attrs):
        attrs['model'] = models.Car
        return type( DjangoModelManager)('Manager', ( DjangoModelManager, ), attrs)

    def assertHasKeys(self, cls, keys):
        self.assertEqual( set( cls.resource_fields.iterkeys()), set(keys))

    def test_auto_genration(self):
        cls = self._make_class()
        self.assertHasKeys( cls, [ 'id', 'name', 'owner', 'max_speed', 'created'])
        self.assertFalse( any( cls.resource_fields[x]['computed'] for x in [ 'name', 'owner', 'max_speed']))
        self.assertFalse( any( cls.resource_fields[x]['optional'] for x in [ 'name', 'max_speed']))
        self.assertTrue( cls.resource_fields['created']['computed'] )
        self.assertTrue( cls.resource_fields['id']['computed'] )
        self.assertEqual( cls.resource_fields['name']['description'], 'name of the var')

    def test_exclude_fields( self):
        cls = self._make_class( model_fields_exclude=[ 'id', 'created'])
        self.assertHasKeys( cls, ['name','owner','max_speed'])

    def test_model_fields( self):
        cls = self._make_class( model_fields = ['name','max_speed'] )
        self.assertHasKeys( cls, ['name','max_speed'])

    def test_custom_resource_fields( self):
        cls = self._make_class( resource_fields = {
            'name': {
                'example' : 'clio'
                },
            'max_speed' : {
                'description' : 'The maximum speed ever'
                },
            'color' : {
                'description' : 'color of the car',
                'example': 'yellow'
                }
            })
        self.assertHasKeys( cls, [ 'id', 'name', 'owner', 'max_speed', 'created', 'color'])
        self.assertEqual( cls.resource_fields['name']['description'], 'name of the var')
        self.assertEqual( cls.resource_fields['name']['example'], 'clio')

        self.assertEqual( cls.resource_fields['max_speed']['description'], 'The maximum speed ever')
        self.assertEqual( cls.resource_fields['color']['example'], 'yellow')


class PM(DjangoModelManager):
    model_fields = [ 'name' ]
    model = models.Parent

class CM(DjangoRelatedModelManager):
    model_fields = [ 'name' ]
    model = models.Child
    related_to = models.Parent

class TestRelatedManager( unittest2.TestCase):
    def setUp(self):
        self.manager = CM(PM(None).get_resource(1))

    def test_related_by(self):
        self.assertEqual( CM.related_by, 'children')

    def test_parent(self):
        self.assertEqual( set(self.manager.list_resource()), set( [1, 2, 3] ))

if __name__ == '__main__':
    unittest2.main()

