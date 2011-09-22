#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.resources import Collection
from napixd.resources.by_collection import SimpleCollection
from napixd.exceptions import NotFound,ValidationError,Duplicate

class Words(Collection):
    fields = ['name']
    def __init__(self,objects=None):
        self.objects = objects or { 1:'One',2:'Two'}

    def get(self,id_):
        try:
            return {'name':self.objects[id_]}
        except KeyError:
            raise NotFound
    def check_id(self,id_):
        try:
            return int(id_)
        except ValueError:
            raise ValidationError('Value must be an int')

    def delete(self,id_):
        del self.objects[id_]

    def modify(self,id_,values):
        if len(values) != 1:
            raise Exception,'Unexpected values'
        if not id_ in self.objects:
            raise NotFound
        self.objects[id_] = values['name']

    def create(self,values):
        name = values['name']
        if len(values) != 1:
            raise Exception,'Unexpected values'
        if name in self.objects.values():
            raise Duplicate
        new_id = max(self.objects)+1
        self.objects[new_id] = name
        return new_id

    def list(self,filters=None):
        if filters and 'max' in filters:
            max_  = filters['max']
            return [x for x in self.objects.keys() if x <= max_]
        return self.objects.keys()

class LettersOfWord(Collection):
    fields = ['ord','count']
    def __init__(self,parent):
        self.name = parent['name']
    def list(self,filters=None):
        return set(self.name)
    def get(self,id_):
        if not id_ in self.name:
            raise NotFound,id_
        return {'ord':ord(id_),'count':sum([1 for x in self.name if x == id_])}

class WordsAndLetters(SimpleCollection):
    fields = ['name']
    letters = LettersOfWord

    def __init__(self,objects=None):
        self.objects = objects or { 1:'One',2:'Two'}

    def child(self,id_):
        try:
            return {'name':self.objects[id_]}
        except KeyError:
            raise NotFound
    def check_id(self,id_):
        try:
            return int(id_)
        except ValueError:
            raise ValidationError('Value must be an int')

    def delete(self,id_):
        del self.objects[id_]

    def modify(self,id_,values):
        if not id_ in self.objects:
            raise NotFound
        self.objects[id_] = values['name']

    def create(self,values):
        name = values['name']
        if name in self.objects.values():
            raise Duplicate
        new_id = max(self.objects)+1
        self.objects[new_id] = name
        return new_id

    def list(self,filters=None):
        if filters and 'max' in filters:
            max_  = filters['max']
            return [x for x in self.objects.keys() if x <= max_]
        return self.objects.keys()
