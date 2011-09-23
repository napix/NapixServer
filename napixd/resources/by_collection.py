#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.exceptions import NotFound
from . import Collection

class SimpleCollectionResource(dict,Collection):
    def child(self,subfile):
        try:
            return getattr(self,subfile)
        except AttributeError:
            raise NotFound,subfile

    def get(self):
        return dict(self)

    def list(self,filters=None):
        return self._subresources

class SubResource(object):
    def __init__(self,subclass):
        self.subclass = subclass
    def __get__(self,instance,owner):
        if instance is None:
            return self.subclass
        return self.subclass(instance)

class SimpleCollection(Collection):
    resource_class = SimpleCollectionResource

    def get(self,ident):
        child = self.child(ident)
        return dict([(key,child[key])
            for key in child
            if key in self.fields])

    def child(self,id_):
        child = self.get_child(id_)
        return self.resource_class(child)

