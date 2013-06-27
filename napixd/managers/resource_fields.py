#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
from napixd.exceptions import ImproperlyConfigured, ValidationError


class ResourceFields( object):
    def __init__(self, resource_fields):
        self.values = [ ResourceField( name, meta) for name, meta in resource_fields.items() ]

    def __get__(self, instance, owner):
        if instance is None:
            return ResourceFieldsDict( owner, self.values )
        return ResourceFieldsDescriptor( instance, self.values )

class ResourceFieldsDict( collections.Mapping):
    def __init__(self, manager_class, values):
        self.resource_fields = values
        self.values = {}
        for resource_field in values:
            field = resource_field.name
            field_meta = resource_field.resource_field()
            validation_method = getattr( manager_class, 'validate_resource_' + field, None)

            if hasattr( validation_method, '__doc__') and validation_method.__doc__ is not None:
                field_meta['validation'] = validation_method.__doc__.strip()
            else:
                field_meta['validation'] = ''

            self.values[ field] = field_meta

    def __getitem__(self, item):
        return self.values[item]
    def __len__(self):
        return len( self.values)
    def __iter__(self):
        return iter( self.values)

    def get_example_resource(self):
        example = {}
        for field in self.resource_fields:
            if field.computed:
                continue
            example[field.name]= field.example
        return example


class ResourceFieldsDescriptor( collections.Sequence):
    def __init__(self, manager, values):
        self.manager = manager
        self.values = values

    def __getitem__(self, item):
        return self.values[item]

    def __len__(self):
        return len(self.values)

    def serialize(self, raw):
        dest = {}
        for k in self.values:
            try:
                 value = raw[k.name]
            except KeyError:
                pass
            else:
                dest[k.name] = k.serialize(value)
        return dest

    def unserialize(self, raw):
        dest = {}
        for k in self:
            try:
                 value = raw[k.name]
            except KeyError:
                pass
            else:
                dest[k.name] = k.unserialize(value)
        return dest

    def validate(self, input, for_edit=False):
        ouput = {}
        for resource_field in self:
            key = resource_field.name
            if resource_field.computed or for_edit and resource_field.editable :
                continue
            elif key not in input:
                if resource_field.default_on_null:
                    value = None
                elif not resource_field.required:
                    continue
                else:
                    raise ValidationError({
                        key : u'Required'
                        })
            else:
                value = input[key]

            ouput[key] = resource_field.validate( self.manager, value)
        return ouput

identity = lambda x:x
class ResourceField( object):
    def __init__(self, name, values):
        self.name = name

        meta = {
            'editable' : True,
            'optional' : False,
            'computed' : False,
            'default_on_null' : False,
            'typing' : 'static',
            'unserializer' : identity,
            'serializer' : identity,
            }
        extra_keys = set( values).difference( meta)
        meta.update( values)

        self.optional = meta['optional']
        self.computed = meta['computed']
        self.default_on_null = meta['default_on_null']

        self.editable = not self.computed and meta.get( 'editable', True)

        explicit_type = meta.get('type')
        if explicit_type and not isinstance( explicit_type, type):
            raise ImproperlyConfigured( '{0}: type field must be a class'.format( self.name))

        try:
            self.example = example = meta['example']
        except KeyError:
            if not self.computed or not explicit_type:
                raise ImproperlyConfigured( '{0}: Missing example'.format( self.name))
            else:
                self.example = ''

        self.type = explicit_type or type(example)
        self.typing = meta['typing']

        if self.typing == 'dynamic':
            self._dynamic_typing = True
        elif self.typing == 'static':
            self._dynamic_typing = False
            if type( self.example) != self.type and not self.computed:
                raise ImproperlyConfigured('{0}: Example is not of type {1}'.format( self.name, self.type.__name__))
        else:
            raise ImproperlyConfigured('{0}: typing must be one of "static", "dynamic"'.format( self.name))

        self.choices = meta.get( 'choices')
        self.unserialize = meta['unserializer']
        self.serialize = meta['serializer']

        self.extra = dict( (k, values[k]) for k in extra_keys )

    def check_type(self, value):
        if self._dynamic_typing:
            return True
        else:
            return isinstance( value, self.type)

    @property
    def required(self):
        return not ( self.optional or self.computed)

    def resource_field(self):
        values = dict( self.extra)
        values.update({
            'editable' : self.editable,
            'optional' : self.optional,
            'computed' : self.computed,
            'default_on_null' : self.default_on_null,
            'example' : self.example,
            'typing' : 'dynamic' if self._dynamic_typing else 'static',
            'choices' : self.choices
            })
        if self.unserialize in ( str, basestring, unicode):
            values['unserializer'] = 'string'
        elif self.unserialize is not identity:
            values['unserializer'] = self.unserialize.__name__

        if self.type in ( str, basestring, unicode):
            values['type'] = 'string'
        elif self.type is not identity:
            values['type'] = self.type.__name__

        if self.serialize in ( str, basestring, unicode):
            values['serializer'] = 'string'
        elif self.serialize is not identity:
            values['serializer'] = self.serialize.__name__

        return values


    def validate( self, manager, value):
        if not self.check_type( value):
            raise ValidationError({
                    self.name : u'Bad type: {0} has type {2} but should be {1}'.format(
                        self.name, self.type.__name__, type(value).__name__)
                    })
        validator = getattr( manager, 'validate_resource_%s' % self.name, None)
        if validator:
            try:
                value = validator( value)
            except ValidationError, e:
                raise ValidationError({
                    self.name : unicode(e)
                    })
        return value
