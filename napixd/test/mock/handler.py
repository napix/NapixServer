#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.handler import Handler,Value,action,IntIdMixin

class MockHandler(IntIdMixin,Handler):
    objects = {}

    name = Value('Name')

    @classmethod
    def find(cls,rid):
        try:
            return cls(rid,name=cls.objects[rid])
        except KeyError:
            return None

    @classmethod
    def find_all(cls):
        return cls.objects.keys()

    @classmethod
    def create(cls,values):
        next_id =len(cls.objects)
        cls.objects[next_id]=values['name']
        cls.next_id = next_id
        return next_id

    def modify(self,value):
        self.__class__.objects[self.rid] = value['name']

    def remove(self):
        del self.__class__.objects[self.rid]

    def __str__(self):
        return self.name

class MockHandlerWithAction(IntIdMixin,Handler):
    objects = {}

    name = Value('Name')

    @classmethod
    def find(cls,rid):
        try:
            return cls(rid,name=cls.objects[rid])
        except KeyError:
            return None

    @classmethod
    def find_all(cls):
        return cls.objects.keys()

    @classmethod
    def create(cls,values):
        next_id =len(cls.objects)
        cls.objects[next_id]=values['name']
        return next_id

    def modify(self,value):
        self.__class__.objects[self.rid] = value['name']

    def delete(self):
        del self.__class__.objects[self.rid]

    @action
    def without_args(self):
        return 909

    @action
    def with_args(self,mand,opt1=None,opt2=None):
        return {'mand':mand,'opt1':opt1,'opt2':opt2}

    def __str__(self):
        return self.name

