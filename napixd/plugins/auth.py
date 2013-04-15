#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import httplib
import json
import socket
import urlparse
import urllib
import functools
import threading

from napixd.conf import Conf
import bottle

from permissions.models import Perm
from permissions.managers import PermSet

class AAAChecker(object):
    logger = logging.getLogger('Napix.AAA.Checker')
    def __init__(self, host, url):
        self.logger.debug( 'Creating a new checker')
        self.host = host
        self.http_client = httplib.HTTPConnection(host)
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
        except socket.gaierror, e:
            self.logger.error( 'Auth server %s not found %s', self.host, e)
            raise bottle.HTTPError( 500, 'Auth server did not respond')
        except socket.error, e:
            self.logger.error( 'Auth server did not respond, %r', e)
            raise bottle.HTTPError( 500, 'Auth server did not respond')
        finally:
            self.logger.debug('Finished the request to the auth server')

        if resp.status != 200 and resp.status != 403 :
            self.logger.error( 'Auth server responded a %s', resp.status)
            self.logger.debug( 'Auth server said: %s', content)
            raise bottle.HTTPError(500, 'Auth server responded unexpected %s code'%resp.status)
        if resp.status != 200:
            return False

        if resp.getheader('content-type') == 'application/json':
            perm_defs = json.loads( content)
            self.logger.debug('Found %s permissions', len( perm_defs))
            return PermSet( Perm( p['host'], p['methods'], p['path'])
                    for p in perm_defs )
        return True

class BaseAAAPlugin(object):
    name = 'authentication_plugin'
    api = 2

    def __init__( self, conf= None, allow_bypass=False):
        self.settings = conf or Conf.get_default('Napix.auth')
        self.service = self.settings.get('service')
        if not self.service:
            self.service = ''
            self.logger.error('Setting Napix.auth.service is empty')
        self.allow_bypass = allow_bypass

    def debug_check(self,request):
        return self.allow_bypass and 'authok' in request.GET

    def reject(self, cause, code=403):
        self.logger.info('Rejecting request of %s: %s',
                bottle.request.environ['REMOTE_ADDR'], cause)
        return bottle.HTTPError( code, cause)

    def authorization_extract(self,request):
        if not 'Authorization' in request.headers:
            raise self.reject( 'You need to sign your request', 401)
        msg,l,signature = request.headers['Authorization'].rpartition(':')
        if l != ':':
            raise self.reject( 'Incorrect NAPIX Authentication', 401)
        content = urlparse.parse_qs(msg)
        for x in content:
            content[x] = content[x][0]
        content['msg'] = msg
        content['signature'] = signature
        return content

    def host_check(self, content):
        try:
            if content['host'] != self.service:
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

    def __init__( self, conf=None, allow_bypass=False , ):
        super( AAAPlugin, self).__init__( conf, allow_bypass)
        url = self.settings.get('auth_url')
        auth_url_parts = urlparse.urlsplit( url)
        self.logger.info('Set up authentication with %s', url)
        self.host = auth_url_parts.netloc
        self.url = urlparse.urlunsplit(( '','',auth_url_parts[2], auth_url_parts[3], auth_url_parts[4]))
        self._local = threading.local()

    @property
    def checker(self):
        if not hasattr( self._local, 'checker'):
            self._local.checker = AAAChecker( self.host, self.url)
        return self._local.checker

    def authserver_check(self, content):
        check = self.checker.authserver_check(content)
        if check == False:
            raise self.reject( 'Access Denied')
        return check

    def apply(self,callback,route):
        @functools.wraps(callback)
        def inner_aaa(*args,**kwargs):
            request = bottle.request
            if self.debug_check( request):
                return callback(*args,**kwargs)
            content = self.authorization_extract( request)

            #self.logger.debug(msg)
            self.host_check( content)
            permissions = self.authserver_check( content)
            path = bottle.request.path
            method = bottle.request.method

            resp = callback(*args,**kwargs)
            if ( method == 'GET' and path.endswith('/') and
                    isinstance( permissions, PermSet) and isinstance( resp, list) ):
                self.logger.debug('Filtering %s urls', len(resp) )
                resp = list( permissions.filter_paths( self.service, resp))
                self.logger.debug('Filtered %s urls', len(resp) )
            return resp

            # actually run the callback
        return inner_aaa

