#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import HttpResponse,HttpResponseServerError
import sys
import json
import logging
import functools
import traceback

from piston.utils import translate_mime,coerce_put_post
from piston import emitters
from django.conf.urls.defaults import url
from exceptions import ValidationError,HTTP400,HTTP405,HTTP404,HTTPException,HTTPRC

logger = logging.getLogger('request')

def wrap_view(fn):
    @functools.wraps(fn)
    def inner(*args,**kwargs):
        try:
            result = fn(*args,**kwargs)
        except HTTPRC,e:
            logger.debug('Caught HTTPRC')
            return e.rc
        except HTTPException,e:
            logger.debug('Caught HTTPEx')
            return HttpResponse(status=e.status)
        except Exception, e:
            logger.debug('Caught Exception %s %s'%(e.__class__.__name__,str(e)))
            traceback.print_tb(sys.exc_info()[2])
            return HttpResponseServerError()
        if isinstance(result,HttpResponse):
            return result
        if hasattr(result,'serialize'):
            result = result.serialize()
        r = HttpResponse(mimetype='application/json')
        json.dump(result,r)
        return r
    return inner

class Service(object):
    def __init__(self,handler):
        self.handler = handler
        self.handler_name = handler.__name__

    def find_resource(self,rid):
        if rid is None :
            raise HTTP400,'Resource identifier required'
        try:
            resource_id = self.handler.validate_resource_id(rid)
        except ValidationError:
            raise HTTP400,'Invalid resource identifier'
        resource = self.handler.find(resource_id)
        if resource == None:
            raise HTTP404
        return resource

    def filter_values(self,data):
        values = {}
        for f in self.handler.fields :
            try:
                values[f] =data[f]
            except KeyError:
                pass
        if not values:
            return None
        return values
    def prepare_request(self,request,allowed_methods):
        if not request.method in allowed_methods:
            raise HTTP405
        coerce_put_post(request)
        if request.method in ('PUT','POST'):
            logger.debug('REQUEST Content-type %s',request.META['CONTENT_TYPE'])
            translate_mime(request)
            request.values = self.filter_values(request.data)

    @wrap_view
    def view_collection(self,request):
        logger.info('Collection %s %s',self.handler_name,request.method)
        self.prepare_request(request,self.handler.collection_methods)
        m = request.method.upper()
        if m == 'GET':
            return self.handler.find_all()
        if m == 'POST':
            rid =  self.handler.create(request.values)
            return {'rid':rid}

    @wrap_view
    def view_resource(self,request,rid):
        logger.info('Resource %s %s %s',self.handler_name,rid,request.method)
        self.prepare_request(request,self.handler.resource_methods)
        resource = self.find_resource(rid)
        m = request.method.upper()
        if m == 'GET':
            return resource
        if m == 'PUT':
            return resource.modify(request.values)
        if m == 'DELETE':
            return resource.remove()

    @wrap_view
    def view_action(self,request,rid,action_id):
        logger.info('Action %s %s %s %s',self.handler_name,rid,action_id,request.method)
        self.prepare_request(request,('POST',))
        resource = self.find_resource(rid)
        cb = getattr(resource,action_id)
        return cb()

def get_urls():
    import handlers
    from handler import registry
    urls =[]
    for ur,handler in registry.items():
        service = Service(handler)
        urls.append(url(r'^%s/(?P<rid>\w+)/(?P<action_id>\w+)/$'%ur,service.view_action))
        urls.append(url(r'^%s/(?P<rid>\w+)/$'%ur,service.view_resource))
        urls.append(url(r'^%s/$'%ur,service.view_collection))
    return urls

