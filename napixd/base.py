#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseHandler(object):
    pass

class HandlerDefinitionError(Exception):
    def __init__(self,cls,msg):
        self.cls = cls
        self.msg = msg
    def __str__(self):
        return 'Registering %s failed: %s'%(self.cls.__name__,self.msg)

def check_handler(cls):
    attributes = {
            'resource_methods':list,
            'collection_methods':list,
            'doc_collection':dict,
            'doc_action':list,
            'url':str,
            '__name__':str,
            'subhandlers':dict,
            'actions':dict,
            'fields':list,
            'validate_resource_id':list,
            }
    methods  = {
            'find_all': lambda x:'GET' in x.collection_methods,
            'create':lambda x:'POST' in x.collection_methods,
            'find': lambda x:bool(x.resource_methods),
            'remove':lambda x:'DELETE' in x.resource_methods,
            'modify':lambda x:'PUT' in x.resource_methods,
            }
    for attr,typ in attributes:
        if not hasattr(cls,attr):
            raise HandlerDefinitionError(cls,'handlers have to define %s attribute'%attr)
        if not isinstance(getattr(cls,attr),typ):
            raise HandlerDefinitionError(cls,'handlers %s attribute have to be a %s'%(attr,typ.__name__))
    for method,checker in methods:
        if checker(cls) and not hasattr(cls,method):
            raise HandlerDefinitionError(cls,'this handler have to define a %s method'%method)
