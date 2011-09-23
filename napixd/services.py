#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import functools

import bottle
from bottle import HTTPError
from napixd.exceptions import NotFound,ValidationError,Duplicate

class ArgumentsPlugin(object):
    name='argument'
    api = 2
    def apply(self,callback,route):
        @functools.wraps(callback)
        def inner(*args,**kw):
            path = self._get_path(args,kw)
            return callback(bottle.request,path)
        return inner

    def _get_path(self,args,kw):
        if args :
            return args
        return map(lambda x:kw[x],
                itertools.takewhile(lambda x:x in kw,
                    itertools.imap(lambda x:'f%i'%x,
                        itertools.count())))

class Service(object):
    def __init__(self,collection):
        self.collection = collection()
        self.url = collection.__name__.lower()

    def setup_bottle(self,app):
        self._setup_bottle(app,self.collection,'/'+self.url,0)

    def _setup_bottle(self,app,collection,prefix,level):
        app.route('%s'%(prefix),method='ANY',callback=self.as_resource,apply=ArgumentsPlugin)
        next_prefix = '%s/:f%i'%(prefix,level)
        app.route('%s/'%(prefix),method='ANY',callback=self.as_collection,apply=ArgumentsPlugin)
        if hasattr(collection,'resource_class'):
            self._setup_bottle(app,collection.resource_class,next_prefix,level+1)
            if hasattr(collection.resource_class,'_subresources'):
                for sr in collection.resource_class._subresources:
                    self._setup_bottle(app,getattr(collection.resource_class,sr),
                            '%s/:f%i'%(next_prefix,level+1),level+2)

    def as_resource(self,request,path):
        return ServiceResourceRequest(request,path,
                self.collection).handle()

    def as_collection(self,request,path):
        return ServiceCollectionRequest(request,path,
                self.collection).handle()

class ServiceRequest(object):
    def __init__(self,request,path,collection):
        self.request = request
        self.method = request.method
        self.base_collection = collection
        self.path = path

    def check_datas(self,collection):
        data = {}
        for x in self.request.data:
            if x in collection.fields:
                data[x] = self.request.data[x]
        return data

    def get_collection(self):
        node = self.base_collection
        for child in self.path:
            child_id = node.check_id(child)
            node = node.child(child_id)
        return node

    def get_callback(self,collection):
        try:
            return getattr(collection,self.METHOD_MAP[self.method])
        except (AttributeError,KeyError):
            available_methods = []
            for meth in self.METHOD_MAP:
                if hasattr(collection,meth):
                    available_methods.append(meth)
            raise HTTPError(405,
                    header=[ ('allow',','.join(available_methods))])

    def handle(self):
        try:
            collection = self.get_collection()
            datas =  self.check_datas(collection)
            callback = self.get_callback(collection)
            args = self.get_args(datas)
            return callback(*args)
        except ValidationError,e:
            raise HTTPError(400,'%s is not a valid identifier'%str(e))
        except KeyError,e:
            raise HTTPError(400,'%s parameter is required'%str(e))
        except NotFound,e:
            raise HTTPError(404,'%s not found'%(str(e)))
        except Duplicate,e:
            raise HTTPError(409,'%s already exists',str(e))


class ServiceCollectionRequest(ServiceRequest):
    METHOD_MAP = {
        'POST':'create',
        'GET':'list'
        }
    def get_args(self,datas):
        if self.method == 'GET':
            return (self.request.GET,)
        elif self.method == 'POST':
            return (datas,)
        return tuple()


class ServiceResourceRequest(ServiceRequest):
    METHOD_MAP = {
            'PUT':'modify',
            'GET':'get',
            'DELETE':'delete',
        }
    def __init__(self,request,path,collection):
        super(ServiceResourceRequest,self).__init__(request,path[:-1],collection)
        self.resource_id = path[-1]

    def get_args(self,datas):
        if self.method == 'PUT':
            return (self.resource_id,datas)
        return (self.resource_id,)
    def get_collection(self):
        collection = super(ServiceResourceRequest,self).get_collection()
        self.resource_id = collection.check_id(self.resource_id)
        return collection


"""

GET     /a/     a.list()
POST    /a/     a.create()

GET     /a/1    a.get(1)
DELETE  /a/1    a.delete(1)
PUT     /a/1    a.modifiy(1)

GET     /a/1/   a.child(1).list()
POST    /a/1/   a.child(1).create()
PUT     /a/1/b  a.child(1).mofify(b)
GET     /a/1/b  a.child(1).b.get()

"""
