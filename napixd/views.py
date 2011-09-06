#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import functools

from napixd.exceptions import ValidationError
from bottle import HTTPError,HTTPResponse,request,redirect

__all__ = ['Service']

logger = logging.getLogger('Napix.Service')

def wrap(fn):
    @functools.wraps(fn)
    def inner(*args,**kwargs):
        return fn(request,*args,**kwargs)
    return inner


def urlize(lst,prefix):
    """ retourne la liste des urls permettant d'acceder correspondant
    à la liste *lst* accedée par view_name"""
    for rid in lst:
        yield '/%s/%s'%(prefix,rid)

class Service(object):
    def __init__(self,handler):
        self.handler = handler
        self.url = handler.url
        self.handler_name = handler.__name__
        if self.__class__ is Service:
            self.subservices = [SubService(handler,subhandler)
                    for subhandler in handler.subhandlers.values()]

    def setup_bottle(self,app):
        self._setup_bottle(self.handler,app)

    def _setup_bottle(self,handler,app):
        logger.info('Installing %s at %s',handler.__name__,self.url)
        app.route(r'/%s/'%self.url,
                callback=wrap(self.view_collection),
                name='%s_collection'%self.url,
                method=handler.collection_methods)
        app.route(r'/%s/:rid'%self.url,
                callback=wrap(self.view_resource),
                name='%s_resource'%self.url,
                method=handler.resource_methods)
        if handler._actions:
            app.route(r'/%s/:rid/:action_id'%self.url,
                    callback=wrap(self.view_action),
                    name='%s_action'%self.url,
                    method=['HEAD','GET','POST'])
        for subserv in self.subservices:
            subserv.setup_bottle(app)

    def _validate_rid(self,handler,rid):
        if rid is None :
            raise HTTPError(400,'Resource identifier required')
        try:
            resource_id = self.handler.validate_resource_id(rid)
        except ValidationError:
            raise HTTPError(400,'Invalid resource identifier')
        return resource_id

    def find_resource(self,rid):
        resource_id = self._validate_rid(self.handler,rid)
        resource = self.handler.find(resource_id)
        if resource == None:
            raise HTTPError,404
        return resource

    def filter_values(self,fields,data):
        values = {}
        for f in fields :
            try:
                values[f] =data[f]
            except KeyError:
                pass
        return values


    def view_collection(self,request):
        if 'doc' in request.GET:
            return self.handler.doc_collection
        logger.info('Collection %s %s',self.handler_name,request.method)
        m = request.method.upper()
        if m == 'HEAD':
            return None
        if m == 'GET':
            res= self.handler.find_all()
            return {'values':zip(res,urlize(res,self.url))}
        if m == 'POST':
            values = self.filter_values(self.handler.fields,request.data)
            rid =  self.handler.create(values)
            return HTTPResponse(None,202,
                    {'Content-location':'/%s/%s'%(self.url,rid)})


    def view_resource(self,request,rid):
        if 'doc' in request.GET:
            return self.handler.doc_resource
        logger.info('Resource %s %s %s',self.handler_name,rid,request.method)
        resource = self.find_resource(rid)
        m = request.method.upper()
        if m == 'HEAD':
            return None
        if m == 'GET':
            return resource
        if m == 'PUT':
            values = self.filter_values(self.handler.fields,request.data)
            resource.modify(values)
        if m == 'DELETE':
            resource.remove()

    def view_action(self,request,rid,action_id):
        logger.info('Action %s %s %s %s',self.handler_name,rid,action_id,request.method)
        resource = self.find_resource(rid)
        cb = getattr(resource,action_id)
        m = request.method.upper()
        if m == 'HEAD':
            return None
        if m == 'GET':
            if 'doc' in request.GET:
                return cb.doc
            return 'Action should be called with POST'
        if m == 'POST':
            values = self.filter_values(cb.fields,request.data)
            return cb(**values)

class SubService(Service):
    def __init__(self,handler,subhandler):
        Service.__init__(self,handler)
        self.subhandler = subhandler
        self.related_handler = subhandler.handler
        self.url = '%s/:mrid/%s'%(handler.url,subhandler.url)
        self.subservices = []

    def setup_bottle(self,app):
        self._setup_bottle(self.subhandler,app)

    def find_sub_resource(self,mrid,rid):
        resource = self.find_resource(self,request,mrid)
        sresource_id = self._validate_rid(self.subhandler,rid)
        res = self.subhandler.find(resource,sresource_id)
        if res is None:
            raise HTTPError,404
        return res

    def view_resource(self,request,mrid,rid):
        subresource = self.find_sub_resource(mrid,rid)
        m = request.method.upper()
        if m == 'HEAD':
            return None
        elif m == 'GET':
            return subresource
        elif m == 'PUT':
            values = self.filter_values(self.subhandler.fields,request.data)
            subresource.modify(values)
        elif m == 'DELETE':
            return subresource.remove()

    def view_collection(self,request,mrid):
        resource = self.find_resource(self,request,mrid)
        m = request.method.upper()
        if m == 'HEAD':
            return None
        if m == 'GET':
            res = self.subhandler.find_all(resource)
            return {'values':zip(res,urlize(res,self.related_handler.url))}
        elif m == 'POST':
            related = self.related_handler.find(request.data['related_id'])
            if related is None:
                raise HTTPError(404,'Need existing related value')
            values = self.filter_values(self.subhandler.fields,request.data)
            return self.subhandler.create(resource,related,values)

    def view_action(self,request,mrid,rid,action_id):
        pass

