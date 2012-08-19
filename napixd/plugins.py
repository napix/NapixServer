#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
import traceback
import functools
import json
import logging
import socket
from cStringIO import StringIO

from urlparse import parse_qs
from httplib2 import Http
from urllib import urlencode

import bottle
from bottle import HTTPResponse,HTTPError

from .conf import Conf
from .http import Response


__all__ = ['ExceptionsCatcher', 'ConversationPlugin', 'AAAPlugin', 'UserAgentDetector']

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
        def inner_conversation(*args,**kwargs):
            request = bottle.request
            #unserialize the request
            if int(request.get('CONTENT_LENGTH',0)) != 0:
                if 'CONTENT_TYPE' in request and request['CONTENT_TYPE'].startswith('application/json'):
                    try:
                        request.data = json.load(request.body)
                    except ValueError:
                        raise HTTPError(400,'Unable to load JSON object')
                else:
                    request.data = request.forms
            else :
                request.data = {}
            headers = []
            content_type = ''
            exception = None
            try:
                result = callback(*args,**kwargs) #Conv
                status = 200
                #result OK
                if isinstance(result,HTTPResponse):
                    exception = result
                elif isinstance( result, Response):
                    bottle.response.headers.update( result.headers)
                    return result
            except HTTPError,e:
                exception = e

            if exception is not None:
                result = exception.output
                status = exception.status
                if exception.headers != None:
                    headers.extend(exception.headers.iteritems())
                    if 'content-type' in exception.headers :
                        content_type = exception.headers['content-type']

            if status != 200 and isinstance( result, basestring):
                if not content_type :
                    content_type = 'text/plain'
            elif result is not None:
                content_type = 'application/json'
                result = self._json_encode(result)
            else:
                content_type = ''
                result = None

            headers.append( ('Content-Type', content_type))
            resp = HTTPResponse( result, status, header=headers)
            return resp
        return inner_conversation

    def _json_encode(self,res):
        buff = StringIO()
        json.dump(res,buff)
        return buff.getvalue()

class ExceptionsCatcher(object):
    name = 'exceptions_catcher'
    api = 2
    logger = logging.getLogger('Napix.Errors')
    def apply(self,callback,route):
        """
        This plugin run the view and catch the exception that are not HTTPResponse.
        The HTTPResponse are legit response, sent to the ConversationPlugin, the rest are errors.
        For this error, it send a dict containing the file, line and details of the exception
        """
        @functools.wraps(callback)
        def inner_exception_catcher(*args,**kwargs):
            try:
                return callback(*args,**kwargs) #Exception
            except HTTPResponse :
                raise
            except Exception,e:
                method = bottle.request.method
                path = bottle.request.path
                a, b, last_traceback = sys.exc_info()
                filename, lineno, function_name, text = traceback.extract_tb(last_traceback)[-1]
                #traceback.print_tb(last_traceback)
                napix_path = os.path.realpath( os.path.join( os.path.dirname( __file__)))
                all_tb = [ dict( zip( ('filename', 'line', 'in', 'call'), x))
                        for x in traceback.extract_tb( last_traceback ) ]
                extern_tb = [ x for x in all_tb
                        if x['filename'].startswith(napix_path) ]
                self.logger.error('%s on %s failed with %s (%s)',  method, path,
                        e.__class__.__name__, str(e) )
                res = {
                        'request' : {
                            'method' : method,
                            'path' : path
                            },
                        'error_text': str(e),
                        'error_class': e.__class__.__name__,
                        'filename': filename,
                        'line': lineno,
                        'traceback' : extern_tb or all_tb,
                        }
                raise HTTPError(500,res)
        return inner_exception_catcher

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
                    not ( 'authok' in request.GET or 'Authorization' in request.headers )):
                raise HTTPError(401, '''
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
</body></html>''', header = [ ( 'CONTENT_TYPE', 'text/html' ) ])
            else:
                return callback( *args, **kwargs)
        return inner_useragent

class AAAPlugin(object):
    """
    Authentication, Authorization and Accounting plugins

    FIXME : A documenter quand ce sera arreté
    """
    name = 'authentication_plugin'
    api = 2
    logger = logging.getLogger('Napix.AAA')
    def __init__( self, conf= None, client= None):
        self.http_client = client or Http()
        self.settings = conf or Conf.get_default('Napix.auth')

    def debug_check(self,request):
        return Conf.get_default('Napix.debug') and 'authok' in request.GET

    def authorization_extract(self,request):
        if not 'Authorization' in request.headers:
            raise HTTPError( 401, 'You need to sign your request')
        msg,l,signature = request.headers['Authorization'].rpartition(':')
        if l != ':':
            self.logger.info('Rejecting request of %s',request.headers['REMOTE_HOST'])
            raise HTTPError(401, 'Incorrect NAPIX Authentication')
        content = parse_qs(msg)
        for x in content:
            content[x] = content[x][0]
        content['msg'] = msg
        content['signature'] = signature
        return content

    def host_check(self, content):
        try:
            if content['host'] != self.settings.get('service'):
                raise HTTPError(403, 'Bad host')
            if ( content['method'] != bottle.request.method or
                    content['path'] != bottle.request.path ):
                raise HTTPError(403, 'Bad authorization data')
        except KeyError:
            raise HTTPError(403, 'No host')

    def authserver_check(self, content):
        headers = { 'Accept':'application/json',
                'Content-type':'application/json', }
        body = json.dumps(content)
        try:
            resp,content = self.http_client.request(self.settings.get('auth_url'),
                    'POST', body=body, headers=headers)
        except socket.error, e:
            self.logger.error( 'Auth server did not respond, %r', e)
            raise HTTPError( 500, 'Auth server did not respond')
        if resp.status == 403:
            raise HTTPError(403,'Access Denied')
        elif resp.status != 200:
            self.logger.error( 'Auth server responded a %s', resp.status)
            raise HTTPError(500, 'Auth server responded unexpected %s code'%resp.status)


    def apply(self,callback,route):
        @functools.wraps(callback)
        def inner_aaa(*args,**kwargs):
            request = bottle.request
            if self.debug_check( request):
                return callback(*args,**kwargs)
            content = self.authorization_extract( request)

            #self.logger.debug(msg)
            self.host_check( content)
            self.authserver_check( content)

            # actually run the callback
            return callback(*args,**kwargs)
        return inner_aaa
