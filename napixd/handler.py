#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect

from napixd.exceptions import ValidationError
from napixd.base import BaseHandler

#__all__=('Handler','action','Value','SubHandler','IntIdMixin')
__all__ = ('Collection','Resource','IntIdMixin')

class Value(object):
    """Class to declare a property inside a handler"""
    def __init__(self,doc):
        self.__doc__ = doc
    def _set_field(self,field):
        self.field = '_napix_'+field
    def __set__(self,instance,value):
        setattr(instance,self.field,value)
    def __get__(self,instance,owner):
        if instance is None:
            return self
        return getattr(instance,self.field)

class SubHandlerProperty(object):
    """Property linking to the the subresource"""
    def __init__(self,subhandler):
        self.subhandler = subhandler
    def __get__(self,instance,owner):
        if instance is None:
            return self.subhandler
        return self.subhandler.find_all(instance)

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


def filter_class(lst,cls):
    """ retourne un dictionnaire sous-ensemble
    du dictionnaire *lst* dont les element sont une instance de *cls*"""
    return dict([x for x in lst.items() if isinstance(x[1],cls)])

def filter_hasattr(lst,attr):
    """ retourne un dictionnaire sous-ensemble
    du dictionnaire *lst* dont les element sont ont un attribut *attr*"""
    return dict([x for x in lst.items() if hasattr(x[1],attr)])

def filter_subclass(lst,cls):
    """ retourne un dictionnaire sous-ensemble
    du dictionnaire *lst* dont les element sont une sous classe de *cls*"""
    return dict([x for x in lst.items() if isinstance(x[1],type) and issubclass(x[1],cls)])

class Definition(object):
    def __init__(self,attrs):
        self.fields = filter_class(attrs,Value)
        self.actions =filter_hasattr(attrs,'_napix_action')
        self.subhandlers=filter_subclass(attrs,BaseHandler)
        self.url = None
        #method applicable to the collection /res/
        self.collection_methods = filter(bool,[
            'HEAD',
            'find_all' in attrs and 'GET',
            'create' in attrs and 'POST',
            ])
        #method applicable to the resource /res/id
        self.resource_methods = filter(bool,[
            'HEAD',
            'find' in attrs and 'GET',
            'modify' in attrs and 'PUT',
            'remove' in attrs and 'DELETE'
            ])

class MetaHandler(type):
    """Metaclass to generate handlers"""
    def __new__(meta,name,bases,attrs):
        """Creation of the type"""
        if 'rid' in attrs:
            raise Exception,'rid is a reserved keyword'

        definition = Definition(attrs)
        attrs['_meta'] = definition

        #url: first of *url given*, *name minus Handler* or *name*
        if 'url' in attrs:
            url = attrs['url']
        elif name.endswith('Handler'):
            url = name[:-7].lower()
        else:
            url = name.lower()
        definition.url = url

        for sub_name,subhandler in definition.subhandlers.items():
            attrs[sub_name.lower()] = SubHandlerProperty(subhandler)

        #install fields as properties
        for name,f in definition.fields.items():
            f._set_field(name)

        cls = type.__new__(meta,name,bases,attrs)
        return cls

    def __init__(self,name,bases,attrs):
        """initialize the in-line documentation"""
        type.__init__(self,name,bases,attrs)
        self.doc_collection = { 'doc' : self.__doc__,
                    'resource_id':self.validate_resource_id.__doc__,
                    'collection_methods':self._meta.collection_methods }
        self.doc_resource = { 'doc':self.__doc__,
                        'fields':dict([(x,y.__doc__) for x,y in self._meta.fields.items()]),
                        'resource_methods':self._meta.resource_methods,
                        'actions':self._meta.actions.keys()}
        self.doc_action = { 'actions' : dict([(x,y.__doc__) for x,y in self._meta.actions.items()]) }

class IntIdMixin:
    @classmethod
    def validate_resource_id(cls,rid):
        """Resource identifier has to be a integer"""
        try:
            return int(rid)
        except ValueError:
            raise ValidationError

class Handler(BaseHandler):
    __metaclass__ = MetaHandler
    """Base for the handlers"""
    doc_collection = None
    doc_resource = None
    doc_action = None

    def __str__(self):
        return str(self.rid)

    def __init__(self,rid=None,**kwargs):
        self.rid = rid
        for k,v in kwargs.items():
            getattr(self.__class__,k).__set__(self,v)

    @classmethod
    def validate_resource_id(cls,rid):
        """Anything that evaluates to True"""
        if not rid:
            raise ValidationError,'RID cannot be empty'
        return rid

    @classmethod
    def make_url(self,rid):
        return '/%s/%s'%(self._meta.url,rid)

    @property
    def get_url(self):
        return self.make_url(self.rid)

    def serialize(self):
        """Serialize by getting the declared properties"""
        r={'rid':self.rid}
        for x in self._meta.fields:
            r[x] = getattr(self,x)
        return r

class SubHandler(Handler):
    handler = None

    def __init__(self,resource,related,rid,**kwargs):
        Handler.__init__(self,rid,**kwargs)
        self.resource = resource
        self.related = related

    def serialize(self):
        d ={ 'resource': [str(self.resource),self.resource.get_url],
                'related' : [str(self.related),self.related.get_url],
                'rid':self.rid }
        d.update(Handler.serialize(self))
        return d

    @property
    def get_url(self):
        return self.make_url(self.resource.rid,self.rid)

    @classmethod
    def make_url(self,mrid,rid):
        return '/%s/%s/%s'%(self.handler.url,mrid,self.url,rid)

class Collection(BaseHandler):
    pass
class Resource(BaseHandler):
    pass
