#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import logging

import django
import django.conf
settings = django.conf.settings

from napixd.conf import Conf
from napixd.managers import Manager
from napixd.managers.mixins import AttrResourceMixin
from napixd.exceptions import ValidationError, NotFound

logger = logging.getLogger('Napix.connectors.django')

class DjangoImport( object):
    _module = None

    def __init__( self, module = None ):
        self.module = module or Conf.get_default('Napix.connectors.django')

    def __enter__(self):
        if not settings.configured:
            self.__class__._module = self.module

            if isinstance( self.module, basestring):
                os.environ['DJANGO_SETTINGS_MODULE'] = self.module
                logger.info('Import django with settings module %s', self.module)
            else:
                settings.configure( **self.module)
                logger.info('Import django with settings dict')

        elif self.module == self.__class__._module :
            logger.debug('Django is already configured')
        else:
            raise RuntimeError, 'Different django settings are already used'

    def __exit__(self, exc_type, exc_value, tb):
        pass

class DjangoModelManagerMeta( type( Manager) ):
    def __new__( self, name, bases, attrs):
        model = attrs.get('model')
        if model:
            resource_fields = self._get_resource_fields_from_model(model)
            if 'resource_fields' in attrs:
                rf = set( attrs['resource_fields'])
                for field in rf.intersection( resource_fields.iterkeys()):
                    resource_fields[field].update( attrs['resource_fields'][field])
                for field in rf.difference( resource_fields.iterkeys() ):
                    resource_fields[field] = attrs['resource_fields'][field]

            if 'model_fields' in attrs:
                resource_fields = dict( (key, resource_fields[key] ) for key in attrs['model_fields'])
            if 'model_fields_exclude' in attrs:
                exclude_fields = set(attrs['model_fields_exclude'])
                resource_fields = dict( (key, resource_fields[key] )
                        for key in resource_fields
                        if key not in exclude_fields )

            attrs['resource_fields'] = resource_fields

            if not attrs.get( 'queryset'):
                attrs['queryset'] = model.objects

        return super( DjangoModelManagerMeta, self).__new__( self, name, bases, attrs)

    @classmethod
    def _get_resource_fields_from_model( self, model):
        resource_fields = {}
        for field, a in model._meta.get_fields_with_model():
            resource_fields[ field.name ] = {
                    'description' : field.help_text,
                    'optional' : field.null or field.blank,
                    'computed' : (
                        getattr( field, 'auto_now', False) or
                        getattr( field, 'auto_now_add', False) or
                        field.auto_created)
                    }
        return resource_fields

class BaseDjangoModelManager( Manager):
    __metaclass__ = DjangoModelManagerMeta

    queryset = None
    def get_queryset( self):
        return self.queryset.all()

    @classmethod
    def get_name(cls):
        return cls.name or cls.model._meta.name.lower()

class DjangoReadOperations( AttrResourceMixin, object):
    def get_resource( self, id_):
        try:
            return self.get_queryset().get( pk=id_ )
        except self.model.DoesNotExist:
            raise NotFound, id_

    def list_resource(self ):
        return self.get_queryset().values_list('pk', flat=True)

class  DjangoWriteOperations( object ):
    def validate_resource( self, resource_dict):
        try:
            for field_name in resource_dict:
                field, b,c,d = self.model._meta.get_field_by_name( field_name)
                proposed = resource_dict[field_name]
                for validator in field.validators:
                    validator( proposed )
        except django.core.exceptions.ValidationError, e:
            raise ValidationError( '%s is not valid: %s' % ( field_name, e))
        else:
            return resource_dict

    def create_resource( self, resource_dict ):
        model = self.get_queryset().create( **resource_dict )
        return model.pk

    def _get_model( self, id_):
        try:
            return self.get_queryset().get( pk=id_)
        except self.model.DoesNotExist:
            raise NotFound, id_

    def delete_resource( self, id_):
        self._get_model( id_).delete()

    def modify_resource( self, id_, resource_dict):
        model = self._get_model(id_)
        for k,v in resource_dict.items():
            setattr( model, k, v)
        model.save()

class DjangoReadOnlyModelManager( DjangoReadOperations, BaseDjangoModelManager):
    pass

class DjangoModelManager( DjangoWriteOperations, DjangoReadOperations, BaseDjangoModelManager):
    pass

class DjangoRelatedModelManagerMeta( DjangoModelManagerMeta):
    def __new__( self, name, bases, attrs ):
        if 'related_to' in attrs:
            model = attrs['model']
            if not 'related_by' in attrs:
                related_to = attrs['related_to']
                relations = [ x.related.get_accessor_name()
                        for x,y in model._meta.get_fields_with_model()
                        if x.rel and (x.rel.to is related_to or x.rel.to.__name__ == related_to ) ]
                attrs['related_by'] = relations[0]

        return super( DjangoRelatedModelManagerMeta, self).__new__( self, name, bases, attrs)

class BaseDjangoRelatedManager( BaseDjangoModelManager ):
    __metaclass__ = DjangoRelatedModelManagerMeta
    @classmethod
    def detect(cls):
        return False

    def get_queryset( self ):
        return getattr( self.parent, self.related_by)

class DjangoRelatedModelManager( DjangoWriteOperations, DjangoReadOperations, BaseDjangoRelatedManager):
    pass
