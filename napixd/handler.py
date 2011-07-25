#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__=('MetaHandler','registry')

class Property(object):
    def __init__(self,field):
        self.field = '_'+field
    def __set__(self,instance,value):
        setattr(instance,self.field,value)
    def __get__(self,instance,owner):
        return getattr(instance,self.field)

registry = {}

def action(fn):
    fn.action = True
    return fn

_value=object()

def value():
    return _value

default_validate = classmethod(lambda x,y:y)

class MetaHandler(type):
    def __call__(self,rid=None,**kwargs):
        instance = super(MetaHandler,self).__call__()
        instance.rid = rid
        for k,v in kwargs.items():
            setattr(instance,'_'+k,v)
        return instance

    def __new__(meta,name,bases,attrs):
        if 'rid' in attrs:
            raise Exception,'rid is a reserved keyword'
        fields = map(lambda x:x[0],filter(lambda x:x[1] is _value,attrs.items()))
        attrs['fields'] = fields
        actions =map(lambda x:x[0],filter(lambda x:hasattr(x[1],'action'),attrs.items()))
        attrs['actions'] = actions
        if not 'validate_resource_id' in attrs:
            attrs['validate_resource_id'] = default_validate
        for f in fields:
            attrs[f]= Property(f)
        def outer(fields):
            def serialize(self):
                r={}
                for x in fields:
                    r[x] = getattr(self,'_'+x)
                return r
            return serialize
        attrs['serialize'] = outer(fields)

        collection_methods = filter(bool,[
                'find_all' in attrs and 'GET',
                'create' in attrs and 'POST',
                ])
        resource_methods = filter(bool,[
                'find' in attrs and 'GET',
                'modify' in attrs and 'PUT',
                'remove' in attrs and 'DELETE'
                ])
        attrs['collection_methods'] = collection_methods
        attrs['resource_methods'] = resource_methods
        cls = type.__new__(meta,name,bases,attrs)
        if 'url' in attrs:
            url = attrs['url']
        elif name.endswith('Handler'):
            url = name[:-7].lower()
        else:
            url = name.lower()
        if url in registry:
            raise Exception,'URL %s is allready register by %s'%(url,repr(registry[url]))
        registry[url] = cls
        return cls
