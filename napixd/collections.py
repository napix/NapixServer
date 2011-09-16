#!/usr/bin/env python
# -*- coding: utf-8 -*-


import inspect
import functools

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

class Collection(object):
    pass

def make_child(real_child):
    @functools.wraps(real_child)
    def inner(self,values):
        child = real_child(self,values)
        return self.resource_class(child)
    return inner

class SimpleMetaCollection(type):
    def __new__(meta,name,bases,attrs):

        resource_class_attrs = {'_subresources':[]}
        actions = {}
        for key,value in attrs.items():
            if isinstance(value,type) and issubclass(value,Collection) and not key == 'resource_class':
                resource_class_attrs[key] = SubResource(value)
                resource_class_attrs['_subresources'].append(key)
            if hasattr(value,'_napix_action'):
                actions[key] = value

        collection_methods = []
        resource_methods = []
        if 'create' in attrs:
            collection_methods.append('POST')
        if 'get' in attrs:
            collection_methods.append('GET')
        if 'child' in attrs:
            attrs['child'] = make_child(attrs['child'])
            resource_methods.append('GET')
        if 'delete' in attrs:
            resource_methods.append('DELETE')
        if 'modify' in attrs:
            resource_methods.append('PUT')

        resource_class = attrs.get('resource_class',Resource)
        attrs['resource_class'] = type(name+'Resource',(resource_class,),resource_class_attrs)
        attrs['resource_methods'] = resource_methods
        attrs['collection_methods'] = collection_methods
        attrs['actions'] = actions

        return type.__new__(meta,name,bases,attrs)

class Resource(dict):
    def child(self,subfile):
        return getattr(self,subfile)

    def get(self):
        return dict(self)

    def list(self):
        return self._subresources

class SubResource(object):
    def __init__(self,subclass):
        self.subclass = subclass
    def __get__(self,instance,owner):
        if instance is None:
            return self.subclass
        return self.subclass(instance)

class SimpleCollection(Collection):
    __metaclass__=SimpleMetaCollection
    def check_id(self,id):
        if id ==  '':
            raise ValueError,'ID cannot be empty'
        return id

