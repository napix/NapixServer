#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import Collection

class SimpleResource(Collection):
    def __init__(self,klass):
        self.klass = klass
        for x in ('list','create','modify','delete'):
            if hasattr(klass,x):
                setattr(self,x,getattr(self,'_'+x))
        if not hasattr(klass,'get'):
            self.get = self._get
        self.fields = self.klass.fields

    def check_id(self,id_):
        return self.klass.check_id(id_)

    def _get(self,id_):
        child=self.klass.child(id_)
        res = {}
        for x in self.fields:
            res[x] = getattr(child,x)
        return res

    def _list(self,filters=None):
        return self.klass.list(filers = None)

    def _create(self,data):
        return self.klass.create(data)

    def _modify(self,id_,data):
        return self.child(id_).modify(data)

    def _delete(self,id_):
        return self.child(id_).delete()

