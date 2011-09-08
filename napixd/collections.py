#!/usr/bin/env python
# -*- coding: utf-8 -*-


import inspect

def action(fn):
    """Decorator to declare an action method inside a handler"""
    param = inspect.getargspec(fn)
    args = param.args
    #self
    args.pop(0)
    #default values
    opt = param.defaults or []

    #mandatory params = param list - param that have default values
    len_mand = len(args) - len(opt)
    fn.mandatory = args[:len_mand]
    fn.optional = dict(zip(args[len_mand:],opt))
    fn._napix_action=True

    return fn

class SimpleMetaCollection(type):
    pass

class SimpleCollection(object):
    __metaclass__=SimpleMetaCollection
    def check_id(self,id):
        if id ==  '':
            raise ValueError,'ID cannot be empty'
        return id

class SubResource(object):
    def __init__(self,subclass):
        self.subclass = subclass
    def __get__(self,instance,owner):
        if instance is None:
            return self.subclass
        return self.subclass(instance)
