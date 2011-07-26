#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__=('MetaHandler','registry')

from napixd.exceptions import ValidationError,HTTP400
import inspect

class Property(object):
    def __init__(self,field):
        self.field = '_'+field
    def __set__(self,instance,value):
        setattr(instance,self.field,value)
    def __get__(self,instance,owner):
        return getattr(instance,self.field)

registry = {}

class Action(object):
    def __init__(self,fn,mandatory=None,optional=None):
        self.__doc__=fn.__doc__
        self.fn = fn
        self.mandatory = mandatory
        self.optional = optional
        fields = mandatory[:]
        fields.extend(optional.keys())
        self.fields = fields
    def __call__(self,**values):
        mandatory_count = len(self.mandatory)
        for k in values:
            if k not in self.fields:
                raise HTTP400,'<%s> is not allowed here'%k
            if not k in self.optional:
                mandatory_count -= 1
        if mandatory_count != 0:
            raise HTTP400,'missing mandatory parameter'
        return self.fn(**values)

def action(fn):
    param = inspect.getargspec(fn)
    args = param.args
    args.pop(0)
    #self
    opt = param.defaults or []

    len_mand = len(args) - len(opt)
    mandatory = args[:len_mand]
    optional = dict(zip(args[len_mand:],opt))

    return Action(fn,mandatory,optional)

_value=object()

def value():
    return _value

def _default_validate(cls,x):
    """Anything"""
    if not x:
        raise ValidationError,'RID cannot be empty'
    return x
default_validate = classmethod(_default_validate)

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
        actions =map(lambda x:x[0],filter(lambda x:isinstance(x[1],Action),attrs.items()))
        attrs['actions'] = actions
        if not 'validate_resource_id' in attrs:
            attrs['validate_resource_id'] = default_validate
        for f in fields:
            attrs[f]= Property(f)
        if not 'serialize' in attrs:
            def outer(fields):
                def serialize(self):
                    r={'rid':self.rid}
                    for x in fields:
                        r[x] = getattr(self,'_'+x)
                    return r
                return serialize
            attrs['serialize'] = outer(fields)

        collection_methods = filter(bool,[
            'HEAD',
            'find_all' in attrs and 'GET',
            'create' in attrs and 'POST',
            ])
        resource_methods = filter(bool,[
            'HEAD',
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
