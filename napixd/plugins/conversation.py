#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
import functools
from cStringIO import StringIO

import bottle

from napixd.http import Response

class ConversationPlugin(object):
    """
    Plugin Bottle to convert
    from and to the python native objects to json

    This plugins ensure all the responses are made in JSON, even the error messages
    """
    name = "conversation_plugin"
    api = 2
    logger = logging.getLogger('Napix.conversations')
    def unwrap(self, request):
        #unserialize the request
        if int(request.get('CONTENT_LENGTH',0)) != 0:
            if 'CONTENT_TYPE' in request and request['CONTENT_TYPE'].startswith('application/json'):
                try:
                    request.data = json.load(request.body)
                except ValueError, e:
                    self.logger.warning( 'Got bad JSON object: %s', e)
                    self.logger.debug('JSON object is %s', request.body.getvalue())
                    raise bottle.HTTPError(400, 'Unable to load JSON object', content_type= 'text/plain' )
            else:
                request.data = request.forms
        else :
            request.data = {}

    def apply(self,callback,route):
        @functools.wraps(callback)
        def inner_conversation(*args,**kwargs):
            request = bottle.request
            exception = None
            try:
                self.unwrap( request)
                result = callback(*args,**kwargs) #Conv
                status = 200
                #result OK
                if isinstance(result, bottle.HTTPResponse):
                    exception = result
                elif isinstance( result, Response):
                    result.seek(0)
                    return bottle.HTTPResponse( result, header=result.headers)
            except bottle.HTTPResponse,e:
                exception = e

            headers = bottle.HeaderDict()
            content_type = ''
            if exception is not None:
                result = exception.body
                status = exception.status
                if exception.headers != None:
                    headers.update(exception.headers)
                    if 'content-type' in exception.headers :
                        content_type = exception.headers['content-type']

            if request.method == 'HEAD':
                content_type = ''
                result = None

            if status != 200 and isinstance( result, basestring):
                if not content_type :
                    content_type = 'text/plain'
            elif result is not None:
                content_type = 'application/json'
                result = self._json_encode(result)
            else:
                content_type = ''
                result = None

            headers.setdefault( 'Content-Type', content_type)
            resp = bottle.HTTPResponse( result, status, **headers)
            return resp
        return inner_conversation

    def _json_encode(self,res):
        buff = StringIO()
        json.dump(res,buff)
        return buff.getvalue()

class UserAgentDetector( object ):
    """
    Display a human readable message when a browser is detected
    """
    name = 'user_agent_detector'
    api = 2
    def apply( self, callback, route):
        @functools.wraps( callback)
        def inner_useragent( *args, **kwargs):
            request = bottle.request
            if ( request.headers.get('user_agent', '' ).startswith('Mozilla') and
                    not request.headers.get('X-Requested-With') == 'XMLHttpRequest' and
                    not ( 'authok' in request.GET or 'Authorization' in request.headers )):
                return bottle.HTTPError(401, '''
<html><head><title>Request Not authorized</title></head><body>
<h1> You need to sign your request</h1>
<p>
Maybe you wish to visit <a href="/_napix_js/">the web interface</a>
</p>
<p>
Or you prefer going to the <a href="/_napix_js/help/high_level.html">the doc</a>
</p>
<p>
Anyway if you just want to explore the Napix server when it's in DEBUG mode, use the <a href="?authok">?authok GET parameter</a>
</p>
</body></html>''', Content_Type= 'text/html' )
            else:
                return callback( *args, **kwargs)
        return inner_useragent
