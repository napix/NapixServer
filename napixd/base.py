#!/usr/bin/env python
# -*- coding: utf-8 -*-

from types import MethodType

class BaseHandler(object):
    pass

class HandlerDefinitionError(Exception):
    def __init__(self,cls,msg):
        self.cls = cls
        self.msg = msg
    def __str__(self):
        return 'Registering %s failed: %s'%(self.cls.__name__,self.msg)

def check_handler(cls):
    meta_attribute = {
            'resource_methods':list,
            'collection_methods':list,
            'url':str,
            'subhandlers':dict,
            'actions':dict,
            'fields':dict,
            }
    attributes = {
            '_meta':object,
            'doc_resource':dict,
            'doc_collection':dict,
            'doc_action':dict,
            'validate_resource_id':MethodType,
            '__name__':str,
            }
    methods  = {
            'find_all': lambda x:'GET' in x.collection_methods,
            'create':lambda x:'POST' in x.collection_methods,
            'find': lambda x:bool(x.resource_methods),
            'remove':lambda x:'DELETE' in x.resource_methods,
            'modify':lambda x:'PUT' in x.resource_methods,
            }
    for attr,typ in attributes.items():
        if not hasattr(cls,attr):
            raise HandlerDefinitionError(cls,'handlers have to define %s attribute'%attr)
        if not isinstance(getattr(cls,attr),typ):
            raise HandlerDefinitionError(cls,'handlers %s attribute have to be a %s'%(attr,typ.__name__))
    meta = cls._meta
    for attr,typ in meta_attribute.items():
        if not hasattr(meta,attr):
            raise HandlerDefinitionError(cls,'handlers meta have to define %s attribute'%attr)
        if not isinstance(getattr(meta,attr),typ):
            raise HandlerDefinitionError(cls,'handlers meta %s attribute have to be a %s'%(attr,typ.__name__))
    for method,checker in methods.items():
        if checker(meta) and not hasattr(cls,method):
            raise HandlerDefinitionError(cls,'this handler have to define a %s method'%method)
