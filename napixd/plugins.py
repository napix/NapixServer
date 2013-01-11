#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
import traceback
import functools
import json
import logging
import socket
import urllib
import urlparse
import threading
from cStringIO import StringIO

from urlparse import parse_qs, urlsplit, urlunsplit
from httplib import HTTPConnection

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
                    raise HTTPError(400, 'Unable to load JSON object', header={ 'content-type' : 'text/plain' })
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
                if isinstance(result,HTTPResponse):
                    exception = result
                elif isinstance( result, Response):
                    result.seek(0)
                    return HTTPResponse( result, header=result.headers)
            except HTTPError,e:
                exception = e

            headers = []
            content_type = ''
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
    def __init__(self, show_errors=False):
        self.show_errors = show_errors
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
                if self.show_errors:
                    traceback.print_exc()
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
                    not request.headers.get('X-Requested-With') == 'XMLHttpRequest' and
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



class AAAChecker(object):
    logger = logging.getLogger('Napix.AAA.Checker')
    def __init__(self, host, url, http_factory=HTTPConnection):
        self.logger.debug( 'Creating a new checker')
        self.http_client = http_factory(host)
        self.url = url

    def authserver_check(self, content):
        headers = { 'Accept':'application/json',
                'Content-type':'application/json', }
        body = json.dumps(content)
        try:
            self.logger.debug('Sending request to the auth server')
            self.http_client.request( 'POST', self.url,
                    body=body, headers=headers)
            resp = self.http_client.getresponse()
            content = resp.read()
        except socket.error, e:
            self.logger.error( 'Auth server did not respond, %r', e)
            raise HTTPError( 500, 'Auth server did not respond')
        finally:
            self.logger.debug('Finished the request to the auth server')

        if resp.status != 200 and resp.status != 403 :
            self.logger.error( 'Auth server responded a %s', resp.status)
            self.logger.debug( 'Auth server said: %s', content)
            raise HTTPError(500, 'Auth server responded unexpected %s code'%resp.status)
        return resp.status == 200

class BaseAAAPlugin(object):
    name = 'authentication_plugin'
    api = 2

    def __init__( self, conf= None, allow_bypass=False):
        self.settings = conf or Conf.get_default('Napix.auth')
        self.allow_bypass = allow_bypass

    def debug_check(self,request):
        return self.allow_bypass and 'authok' in request.GET

    def reject(self, cause, code=403):
        self.logger.info('Rejecting request of %s: %s',
                bottle.request.environ['REMOTE_ADDR'], cause)
        return HTTPError( code, cause)

    def authorization_extract(self,request):
        if not 'Authorization' in request.headers:
            raise self.reject( 'You need to sign your request', 401)
        msg,l,signature = request.headers['Authorization'].rpartition(':')
        if l != ':':
            raise self.reject( 'Incorrect NAPIX Authentication', 401)
        content = parse_qs(msg)
        for x in content:
            content[x] = content[x][0]
        content['msg'] = msg
        content['signature'] = signature
        return content

    def host_check(self, content):
        try:
            if content['host'] != self.settings.get('service'):
                raise self.reject('Bad host')
            path = urllib.quote(bottle.request.path ,'%/')
            if bottle.request.query_string:
                path += '?' + bottle.request.query_string
            if content['method'] != bottle.request.method or content['path'] != path:
                raise self.reject( 'Bad authorization data')
        except KeyError, e:
            raise self.reject( 'Missing authentication data: %s' %e)

class AAAPlugin(BaseAAAPlugin):
    """
    Authentication, Authorization and Accounting plugins

    FIXME : A documenter quand ce sera arreté
    """
    logger = logging.getLogger('Napix.AAA')

    def __init__( self, conf=None, allow_bypass=False , auth_checker_factory=AAAChecker):
        super( AAAPlugin, self).__init__( conf, allow_bypass)
        auth_url_parts = urlsplit(self.settings.get('auth_url'))
        self.host = auth_url_parts.netloc
        self.url = urlunsplit(( '','',auth_url_parts[2], auth_url_parts[3], auth_url_parts[4]))
        self._local = threading.local()
        self.auth_checker_factory = auth_checker_factory

    @property
    def checker(self):
        if not hasattr( self._local, 'checker'):
            self._local.checker = self.auth_checker_factory( self.host, self.url)
        return self._local.checker

    def authserver_check(self, content):
        check = self.checker.authserver_check(content)
        if not check:
            raise self.reject( 'Access Denied')

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

class PathInfoMiddleware(object):
    def __init__(self, application):
        self.application = application
    def __call__(self, environ, start_response):
        path = urlparse.urlparse(environ['REQUEST_URI']).path.replace('%2f', '%2F')
        path_info = '%2F'.join( urllib.unquote( path_bit) for path_bit in path.split('%2F'))
        environ['PATH_INFO'] = path_info
        return self.application( environ, start_response)

class CORSMiddleware(object):
    def __init__(self, application):
        self.application = application
    def __call__(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'OPTIONS':
            start_response( '200 OK', [
                ('Access-Control-Allow-Origin',  '*'),
                ('Access-Control-Allow-Methods',  'GET, POST, PUT, CREATE, DELETE, OPTIONS'),
                ('Access-Control-Allow-Headers',  'Authorization, Content-Type'),
                ])
            return []
        return self.application( environ, start_response)
