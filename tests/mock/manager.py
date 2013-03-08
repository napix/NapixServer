#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.managers import Manager
from napixd.exceptions import NotFound,ValidationError,Duplicate

class Words(Manager):
    resource_fields = {
            'name':{'description':'word','example':'four'},
            'letter_count':{ 'computed':True, 'description':'Letter count'}
            }

    def __init__(self,parent = None):
        super(Words,self).__init__(parent)
        if parent:
            self.objects = dict(parent['words'])
        else:
            self.objects = {}

    def validate_resource_name( self, name):
        if name.startswith( '_napix_'):
            raise ValidationError, 'Not word can start with _napix_'
        return name

    def get_resource(self,id_):
        try:
            name = self.objects[id_]
            return {'name': name,
                    'letter_count':len(name),
                    'first_letter':name[0]}
        except KeyError:
            raise NotFound

    def validate_id(self,id_):
        try:
            return int(id_)
        except ValueError:
            raise ValidationError('Value must be an int')

    def delete_resource(self,id_):
        del self.objects[id_]

    def modify_resource(self,id_,values):
        if len(values) != 1:
            raise Exception,'Unexpected values'
        if not id_ in self.objects:
            raise NotFound
        self.objects[id_] = values['name']

    def create_resource(self,values):
        name = values['name']
        if len(values) != 1:
            raise Exception,'Unexpected values'
        if name in self.objects.values():
            raise Duplicate
        new_id = max(self.objects)+1
        self.objects[new_id] = name
        return new_id

    def list_resource(self,filters=None):
        if filters and 'max' in filters:
            max_  = filters['max']
            return [x for x in self.objects.keys() if x <= max_]
        return self.objects.keys()

