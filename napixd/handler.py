#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__=('MetaHandler','registry')

from django.core.urlresolvers import reverse
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

class ActionInstance(object):
    def __init__(self,action,instance):
        self.action = action
        self.instance = instance
    def __getattr__(self,attr):
        return getattr(self.action,attr)
    def __call__(self,**values):
        self.action(self.instance,**values)

class Action(object):
    @property
    def doc(self):
        return { 'mandatory_params':self.mandatory,
                'optional_params':self.optional,
                'action' : self.__doc__}
    def __init__(self,fn,mandatory=None,optional=None):
        self.__doc__=fn.__doc__
        self.fn = fn
        self.mandatory = mandatory
        self.optional = optional
        fields = mandatory[:]
        fields.extend(optional.keys())
        self.fields = fields
    def __get__(self,instance,owner):
        return ActionInstance(self,instance)

    def __call__(self,instance,**values):
        print self,values
        missing = filter(lambda x: x not in values,self.mandatory)
        if missing:
            raise HTTP400,'missing mandatory parameter "%s"'%(','.join(missing))
        forbidden = filter(lambda x: x not in self.fields,values)
        if forbidden:
            raise HTTP400,'"%s" is not allowed here'%(','.join(forbidden))
        return self.fn(instance,**values)

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

class Value():
    @property
    def doc(self):
        return self.__doc__
    def __init__(self,doc):
        self.__doc__ = doc

def _default_validate(cls,x):
    """Anything"""
    if not x:
        raise ValidationError,'RID cannot be empty'
    return x
default_validate = classmethod(_default_validate)

def filter_class(lst,cls):
    return dict([x for x in lst.items() if isinstance(x[1],cls)])

def urlize(lst,view_name):
    result = []
    for x in lst:
        result.append(reverse(view_name,args=[x]))
    return result

def default_init(self,rid=None,**kwargs):
    instance = super(MetaHandler,self).__call__()
    instance.rid = rid
    for k,v in kwargs.items():
        setattr(instance,'_'+k,v)
    return instance

class MetaHandler(type):
    """MAGIC HAPPENS HERE"""
    def __new__(meta,name,bases,attrs):
        if 'rid' in attrs:
            raise Exception,'rid is a reserved keyword'
        fields = filter_class(attrs,Value)
        attrs['fields'] = fields
        actions =filter_class(attrs,Action)
        attrs['actions'] = actions
        if not 'validate_resource_id' in attrs:
            attrs['validate_resource_id'] = default_validate
        for f in fields:
            attrs[f]= Property(f)
        if not '__init__' in attrs:
            attrs['__init__'] = default_init
        if not 'serialize' in attrs:
            def outer(fields):
                def serialize(self):
                    r={'rid':self.rid}
                    for x in fields:
                        r[x] = getattr(self,'_'+x)
                    return r
                return serialize
            attrs['serialize'] = outer(fields)

        if 'url' in attrs:
            url = attrs['url']
        elif name.endswith('Handler'):
            url = name[:-7].lower()
        else:
            url = name.lower()
        if url in registry:
            raise Exception,'URL %s is allready register by %s'%(url,repr(registry[url]))

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

        attrs['doc_collection'] = { 'doc' : attrs['__doc__'],
                    'resource_id':attrs['validate_resource_id'].__doc__,
                    'collection_methods':attrs['collection_methods'] }
        attrs['doc_resource'] = { 'doc':attrs['__doc__'],
                        'fields':dict([(x,y.doc) for x,y in fields.items()]),
                        'resource_methods':attrs['resource_methods'],
                        'actions':actions.keys()}
        attrs['doc_action'] = { 'actions' : dict([(x,y.doc) for x,y in actions.items()]) }

        if 'find_all' in attrs:
            def make_find_all(fn,view_name):
                if isinstance(fn,classmethod):
                    fn = fn.__func__
                def inner(*args,**kwargs):
                    return urlize(fn(*args,**kwargs),view_name)
                return classmethod(inner)
            attrs['find_all']=make_find_all(attrs['find_all'],'%s_resource'%(url))

        cls = type.__new__(meta,name,bases,attrs)
        registry[url] = cls
        return cls
