#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect

from napixd.exceptions import ValidationError

__all__=('BaseHandler','action','Value')

class Property(object):
    def __init__(self,field):
        self.field = '_'+field
    def __set__(self,instance,value):
        setattr(instance,self.field,value)
    def __get__(self,instance,owner):
        if instance is None:
            return self
        return getattr(instance,self.field)

class ActionInstance(object):
    """Proxy d'une action pour une ressource donnée"""
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
        missing = filter(lambda x: x not in values,self.mandatory)
        if missing:
            raise KeyError,'missing mandatory parameter "%s"'%(','.join(missing))
        forbidden = filter(lambda x: x not in self.fields,values)
        if forbidden:
            raise ValueError,'"%s" is not allowed here'%(','.join(forbidden))
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


def filter_class(lst,cls):
    """ retourne un dictionnaire sous-ensemble
    du dictionnaire *lst* dont les element sont une instance de *cls*"""
    return dict([x for x in lst.items() if isinstance(x[1],cls)])


class MetaHandler(type):
    """MAGIC HAPPENS HERE"""
    def __new__(meta,name,bases,attrs):
        if 'rid' in attrs:
            raise Exception,'rid is a reserved keyword'
        fields = filter_class(attrs,Value)
        attrs['_fields'] = fields
        actions =filter_class(attrs,Action)
        attrs['_actions'] = actions
        for f in fields:
            attrs[f]= Property(f)

        if 'url' in attrs:
            url = attrs['url']
        elif name.endswith('Handler'):
            url = name[:-7].lower()
        else:
            url = name.lower()
        attrs['url']=url

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
        return cls

    def __init__(self,name,bases,attrs):
        type.__init__(self,name,bases,attrs)
        attrs['doc_collection'] = { 'doc' : self.__doc__,
                    'resource_id':self.validate_resource_id.__doc__,
                    'collection_methods':self.collection_methods }
        attrs['doc_resource'] = { 'doc':self.__doc__,
                        'fields':dict([(x,y.doc) for x,y in self._fields.items()]),
                        'resource_methods':self.resource_methods,
                        'actions':self._actions.keys()}
        attrs['doc_action'] = { 'actions' : dict([(x,y.doc) for x,y in self._actions.items()]) }

class BaseHandler(object):
    """Base for the handlers"""
    __metaclass__ = MetaHandler
    fields = {}
    actions = {}
    doc_collection = None
    doc_resource = None
    doc_action = None
    def __init__(self,rid=None,**kwargs):
        self.rid = rid
        for k,v in kwargs.items():
            setattr(self,'_'+k,v)

    @classmethod
    def validate_resource_id(cls,rid):
        """Anything that evaluates to True"""
        if not rid:
            raise ValidationError,'RID cannot be empty'
        return rid

    def serialize(self):
        r={'rid':self.rid}
        for x in self.fields:
            r[x] = getattr(self,'_'+x)
        return r
