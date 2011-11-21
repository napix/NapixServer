#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import traceback
import functools
import json
import logging
from cStringIO import StringIO

from urlparse import parse_qs
from httplib2 import Http
from urllib import urlencode

import bottle
from bottle import request,HTTPResponse,HTTPError

from napixd import settings

__all__ = ['ExceptionsCatcher', 'ConversationPlugin', 'AAAPlugin']

class ConversationPlugin(object):
    """
    Plugin Bottle to convert
    from and to the python native objects to json

    This plugins ensure all the responses are made in JSON, even the error messages
    """
    name = "conversation_plugin"
    api = 2
    def apply(self,callback,route):
        @functools.wraps(callback)
        def inner(*args,**kwargs):
            #unserialize the request
            if 'CONTENT_TYPE' in request and request['CONTENT_TYPE'].startswith('application/json'):
                try:
                    request.data = json.load(request.body)
                except ValueError:
                    raise HTTPError(400,'Unable to load JSON object')
            else:
                request.data = request.forms
            headers = [('Content-type', 'application/json')]
            try:
                result = callback(*args,**kwargs) #Conv
                status = 200
                #result OK
            except HTTPError,e:
                result = e.output
                status = e.status
                if e.headers != None:
                    headers.extend(e.headers.iteritems())
            resp = HTTPResponse(result and self._json_encode(result) or None,
                    status, header=headers)
            return resp
        return inner

    def _json_encode(self,res):
        buff = StringIO()
        json.dump(res,buff)
        return buff.getvalue()

class ExceptionsCatcher(object):
    name = 'exceptions_catcher'
    api = 2
    def apply(self,callback,route):
        """
        This plugin run the view and catch the exception that are not HTTPResponse.
        The HTTPResponse are legit response, sent to the ConversationPlugin, the rest are errors.
        For this error, it send a dict containing the file, line and details of the exception
        """
        @functools.wraps(callback)
        def inner(*args,**kwargs):
            try:
                return callback(*args,**kwargs) #Exception
            except HTTPResponse :
                raise
            except Exception,e:
                a, b, last_traceback = sys.exc_info()
                filename, lineno, function_name, text = traceback.extract_tb(last_traceback)[-1]
                #traceback.print_tb(last_traceback)
                res = {
                        'error_text': str(e),
                        'error_class': e.__class__.__name__,
                        'filename': filename,
                        'line': lineno,
                        }
                raise HTTPError(500,res)
        return inner

class AAAPlugin(object):
    """
    Authentication, Authorization and Accounting plugins

    FIXME : A documenter quand ce sera arreté
    """
    name = 'authentication_plugin'
    api = 2
    logger = logging.getLogger('AAA')
    def apply(self,callback,route):
        @functools.wraps(callback)
        def inner(*args,**kwargs):
            if bottle.DEBUG and 'authok' in request.GET:
                return None
            if not 'HTTP_AUTHORIZATION' in request.META:
                raise HTTPError(401)
            msg,l,signature = request.headers['HTTP_AUTHORIZATION'].rpartition(':')
            if l != ':':
                self.logger.info('Rejecting request of %s',request.headers['REMOTE_HOST'])
                raise HTTPError(401,'Need moar authentication')
            content = parse_qs(msg)
            for x in content:
                content[x] = content[x][0]
            try:
                if content['host'] != settings.SERVICE:
                    raise HTTPError(400,'Bad host')
            except AttributeError:
                raise HTTPError(400,'No host')
            content['msg'] = msg
            content['signature'] = signature
            self.logger.debug(msg)
            h=Http()
            headers = { 'Accept':'application/json',
                    'Content-type':'application/x-www-form-urlencoded', }
            body = urlencode(content)
            resp,content = h.request(settings.AUTH_URL,'POST',body=body,headers=headers)
            if resp.status != 200:
                return HTTPError(403,'No auth')
        return inner
