#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from napixd.exceptions import ValidationError
from bottle import HTTPError,HTTPResponse

logger = logging.getLogger('request')

def urlize(lst,prefix):
    """ retourne la liste des urls permettant d'acceder correspondant
    à la liste *lst* accedée par view_name"""
    for rid in lst:
        yield '/%s/%s'%(prefix,rid)

class Service(object):
    def __init__(self,handler):
        self.handler = handler
        self.handler_name = handler.__name__

    def find_resource(self,rid):
        if rid is None :
            raise HTTPError,400,'Resource identifier required'
        try:
            resource_id = self.handler.validate_resource_id(rid)
        except ValidationError:
            raise HTTPError,400,'Invalid resource identifier'
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
    def prepare_request(self,request,allowed_methods):
        if not request.method in allowed_methods:
            raise HTTPError,405

    def view_collection(self,request):
        if 'doc' in request.GET:
            return self.handler.doc_collection
        logger.info('Collection %s %s',self.handler_name,request.method)
        self.prepare_request(request,self.handler.collection_methods)
        m = request.method.upper()
        if m == 'HEAD':
            return None
        if m == 'GET':
            res= self.handler.find_all()
            return {'values':zip(res,urlize(res,self.handler.url))}
        if m == 'POST':
            values = self.filter_values(self.handler.fields,request.data)
            rid =  self.handler.create(values)
            return HTTPResponse(202,None,
                    {'Content-location':'/%s/%s'%(self.handler.url,rid)})


    def view_resource(self,request,rid):
        if 'doc' in request.GET:
            return self.handler.doc_resource
        logger.info('Resource %s %s %s',self.handler_name,rid,request.method)
        self.prepare_request(request,self.handler.resource_methods)
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
        self.prepare_request(request,('POST','HEAD','GET'))
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
