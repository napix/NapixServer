#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect

from napixd.exceptions import ValidationError

__all__=('Handler','action','Value','SubHandler','IntIdMixin')

class Property(object):
    def __init__(self,field):
        self.field = '_hdlr_'+field
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

class SubHandlerProperty(object):
    """Property linking to the the subresource"""
    def __init__(self,subhandler):
        self.subhandler = subhandler
    def __get__(self,instance,owner):
        if instance is None:
            return self.subhandler
        return self.subhandler.find_all(instance)

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
    """Decorator to declare an action method inside a handler"""
    param = inspect.getargspec(fn)
    args = param.args
    #self
    args.pop(0)
    #default values
    opt = param.defaults or []

    #mandatory params = param list - param that have default values
    len_mand = len(args) - len(opt)
    mandatory = args[:len_mand]
    optional = dict(zip(args[len_mand:],opt))

    return Action(fn,mandatory,optional)

class Value():
    """Class to declare a property inside a handler"""
    @property
    def doc(self):
        return self.__doc__
    def __init__(self,doc):
        self.__doc__ = doc


def filter_class(lst,cls):
    """ retourne un dictionnaire sous-ensemble
    du dictionnaire *lst* dont les element sont une instance de *cls*"""
    return dict([x for x in lst.items() if isinstance(x[1],cls)])

def filter_subclass(lst,cls):
    """ retourne un dictionnaire sous-ensemble
    du dictionnaire *lst* dont les element sont une instance de *cls*"""
    return dict([x for x in lst.items() if isinstance(x[1],type) and issubclass(x[1],cls)])


class MetaHandler(type):
    """Metaclass to generate handlers"""
    def __new__(meta,name,bases,attrs):
        """Creation of the type"""
        if 'rid' in attrs:
            raise Exception,'rid is a reserved keyword'
        fields = filter_class(attrs,Value)
        attrs['_fields'] = fields
        actions =filter_class(attrs,Action)
        attrs['_actions'] = actions
        attrs['subhandlers']=filter_subclass(attrs,BaseHandler)
        for sub_name,subhandler in attrs['subhandlers'].items():
            attrs[sub_name.lower()] = SubHandlerProperty(subhandler)
        #install fields as properties
        for f in fields:
            attrs[f]= Property(f)

        #url: first of *url given*, *name minus Handler* or *name*
        if 'url' in attrs:
            url = attrs['url']
        elif name.endswith('Handler'):
            url = name[:-7].lower()
        else:
            url = name.lower()
        attrs['url']=url

        #method applicable to the collection /res/
        collection_methods = filter(bool,[
            'HEAD',
            'find_all' in attrs and 'GET',
            'create' in attrs and 'POST',
            ])
        #method applicable to the resource /res/id
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
        """initialize the in-line documentation"""
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
    pass

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
    _fields = {}
    _actions = {}
    doc_collection = None
    doc_resource = None
    doc_action = None

    def __str__(self):
        return str(self.rid)

    def __init__(self,rid=None,**kwargs):
        self.rid = rid
        for k,v in kwargs.items():
            setattr(self,'_hdlr_'+k,v)

    @classmethod
    def validate_resource_id(cls,rid):
        """Anything that evaluates to True"""
        if not rid:
            raise ValidationError,'RID cannot be empty'
        return rid

    @classmethod
    def make_url(self,rid):
        return '/%s/%s'%(self.url,rid)

    @property
    def get_url(self):
        return self.make_url(self.rid)

    def serialize(self):
        """Serialize by getting the declared properties"""
        r={'rid':self.rid}
        for x in self._fields:
            r[x] = getattr(self,'_hdlr_'+x)
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

