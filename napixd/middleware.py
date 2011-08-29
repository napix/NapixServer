#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import traceback

from httplib2 import Http
from urllib import urlencode
from urlparse import parse_qs

from django.conf import settings
from django.http import HttpResponse,HttpResponseServerError

from piston.emitters import Emitter
from piston.utils import translate_mime,coerce_put_post

from napixd.exceptions import HTTPException,HTTPRC,HTTPRedirect,HTTPWithContent,HTTPForbidden,PermissionDenied

request_logger = logging.getLogger('request')

auth_url = 'http://auth.napix.local/auth/authorization/'

class AuthMiddleware(object):
    def process_request(self,request):
        if settings.DEBUG and 'authok' in request.GET:
            return None
        if not 'HTTP_AUTHORIZATION' in request.META:
            return HttpResponse(status=401)
        msg,l,signature = request.META['HTTP_AUTHORIZATION'].rpartition(':')
        if l != ':':
            return HttpResponse('Need moar authentication',status=401,mimetype='text/plain')
        content = parse_qs(msg)
        for x in content:
            content[x] = content[x][0]
        try:
            if content['host'] != settings.SERVICE:
                return HttpResponse('Bad host',status=400,mimetype='text/plain')
        except AttributeError:
            return HttpResponse('No host',status=400,mimetype='text/plain')
        content['msg'] = msg
        content['signature'] = signature
        request_logger.debug(msg)
        h=Http()
        headers = { 'Accept':'application/json',
                'Content-type':'application/x-www-form-urlencoded', }
        body = urlencode(content)
        resp,content = h.request(auth_url,'POST',body=body,headers=headers)
        if resp.status != 200:
            return HttpResponse('No auth',status=403,mimetype='text/plain')

class ConversationMiddleware(object):
    status_code = 200

    def process_request(self,request):
        coerce_put_post(request)
        if request.method in ('PUT','POST'):
            request_logger.debug('REQUEST Content-type %s',request.META['CONTENT_TYPE'])
            translate_mime(request)

    def process_response(self,request,response):
        request_logger.debug('request %s %s',request.method,request.get_full_path())
        if isinstance(response,HttpResponse):
            request_logger.debug('Found HttpResponse')
            return response
        return self.respond(request,response)


    def process_exception(self,request,exception):
        request_logger.debug('Caught %s',exception.__class__.__name__)
        if isinstance(exception,HTTPRC):
            return self.respond(request,None,exception.rc)
        if isinstance(exception,HTTPException):
            return self.respond(request,str(exception),exception.status)
        if isinstance(exception,HTTPRedirect):
            return self.respond(request,exception.content,301,{'Location':exception.url})
        if isinstance(exception,HTTPWithContent):
            return self.respond(request,exception.content,exception.status)
        if isinstance(exception,Exception):
            request_logger.debug('Caught Exception %s %s'%(
                exception.__class__.__name__,str(exception)))
            resp = HttpResponseServerError(mimetype='text/plain')
            a,b,c = sys.exc_info()
            traceback.print_exception(a,b,c,None,resp)
            return resp
        request_logger.error('Found somethind weird :( %s',repr(exception))

    def determine_ctype(self,request):
        ctypes = [ request.GET.get('format',None)]
        if 'HTTP_ACCEPT' in request.META:
            ctypes.extend([a.split(';')[0] for a in request.META['HTTP_ACCEPT'].split(',')])
        ctypes.append('application/json')
        m=lambda x:x and '/' in x and x.split('/')[1]
        ctypes = filter(lambda x:x and x != '*',map(m,ctypes))
        for ctype in ctypes:
            try:
                emitter,ct=Emitter.get(ctype)
                break
            except ValueError:
                pass
        return emitter,ct

    def respond(self,request,content,status_code=status_code,headers=None):
        if hasattr(content,'serialize'):
            request_logger.debug('Found serialisable thing')
            content = content.serialize()
        headers = headers or {}

        emitter,ct = self.determine_ctype(request)
        srl = emitter(content, None, None, None,None)
        stream = srl.render(request)
        resp = HttpResponse(stream,status=status_code,mimetype=ct)
        for h,v in headers:
            resp[h] = v
        return resp
