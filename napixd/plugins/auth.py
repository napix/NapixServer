#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import httplib
import json
import socket
import urlparse
import functools
import threading

from napixd.conf import Conf
from napixd.chrono import Chrono
import bottle

from permissions.models import Perm
from permissions.managers import PermSet

TIMEOUT = 5


class Check(object):

    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__, self.content)


class Success(Check):

    def __init__(self, content):
        if content and isinstance(content, list):
            content = PermSet(Perm(p['host'], p['methods'], p['path'])
                              for p in content)
        else:
            content = None
        super(Success, self).__init__(content)

    def __nonzero__(self):
        return True


class Fail(Check):

    def __init__(self, content):
        self.raw = content
        if not content or not isinstance(content, list):
            content = None
        else:
            content = PermSet(Perm('*', '*', p) for p in content)
        super(Fail, self).__init__(content)

    def __nonzero__(self):
        return False


class AAAChecker(object):
    logger = logging.getLogger('Napix.AAA.Checker')

    def __init__(self, host, url):
        self.logger.debug('Creating a new checker')
        self.host = host
        self.http_client = httplib.HTTPConnection(host, timeout=TIMEOUT)
        self.url = url

    def authserver_check(self, content):
        headers = {'Accept': 'application/json',
                   'Content-type': 'application/json', }
        body = json.dumps(content)
        try:
            self.logger.debug('Sending request to the auth server')
            self.http_client.request('POST', self.url,
                                     body=body, headers=headers)
            resp = self.http_client.getresponse()
            content = resp.read()
        except socket.gaierror, e:
            self.logger.error('Auth server %s not found %s', self.host, e)
            raise bottle.HTTPError(500, 'Auth server did not respond')
        except socket.timeout as e:
            self.logger.error('Auth server timed out, %r', e)
            raise bottle.HTTPError(504, 'Auth server timeout')
        except socket.error as e:
            self.logger.error('Auth server did not respond, %r', e)
            raise bottle.HTTPError(500, 'Auth server did not respond')
        finally:
            self.http_client.close()
            self.logger.debug('Finished the request to the auth server')

        if resp.status != 200 and resp.status != 403:
            self.logger.error('Auth server responded a %s', resp.status)
            self.logger.debug('Auth server said: %s', content)
            raise bottle.HTTPError(
                500, 'Auth server responded unexpected %s code' % resp.status)

        if resp.getheader('content-type') == 'application/json':
            content = json.loads(content)

        if resp.status != 200:
            return Fail(content)

        return Success(content)


class BaseAAAPlugin(object):
    name = 'authentication_plugin'
    api = 2

    def __init__(self, conf=None, service_name=''):
        self.settings = conf or Conf.get_default('Napix.auth')

        hosts = self.settings.get('hosts')
        if hosts:
            if isinstance(hosts, list):
                self.hosts = set(hosts)
            elif isinstance(hosts, basestring):
                self.hosts = set([hosts])
            else:
                self.logger.error(
                    'Napix.auth.hosts is not a string or a list of strings')
                self.hosts = None
        else:
            self.logger.warning('No host settings, every host is allowed')
            self.hosts = None

        self.service = service_name

    def reject(self, cause, code=403):
        self.logger.info('Rejecting request of %s: %s',
                         bottle.request.environ['REMOTE_ADDR'], cause)
        return bottle.HTTPError(code, cause)

    def authorization_extract(self, request):
        if not 'Authorization' in request.headers:
            raise self.reject('You need to sign your request', 401)
        msg, l, signature = request.headers['Authorization'].rpartition(':')
        if l != ':':
            raise self.reject('Incorrect NAPIX Authentication', 401)
        content = urlparse.parse_qs(msg)
        for x in content:
            content[x] = content[x][0]
        content['msg'] = msg
        content['signature'] = signature
        return content

    def host_check(self, content):
        try:
            if self.hosts is not None and content['host'] not in self.hosts:
                raise self.reject('Bad host')
            path = bottle.request.path
            if bottle.request.query_string:
                path += '?' + bottle.request.query_string

            if content['method'] != bottle.request.method:
                raise self.reject(
                    'Bad authorization data method does not match')
            signed = content['path']
            if signed != path:
                raise self.reject('Bad authorization data path does not match')
        except KeyError, e:
            raise self.reject('Missing authentication data: %s' % e)


class AAAPlugin(BaseAAAPlugin):

    """
    Authentication, Authorization and Accounting plugins

    FIXME : A documenter quand ce sera arreté
    """
    logger = logging.getLogger('Napix.AAA')

    def __init__(self, conf=None, service_name=''):
        super(AAAPlugin, self).__init__(conf, service_name=service_name)
        url = self.settings.get('auth_url')
        auth_url_parts = urlparse.urlsplit(url)
        self.logger.info('Set up authentication with %s', url)
        self.host = auth_url_parts.netloc
        self.url = urlparse.urlunsplit(
            ('', '', auth_url_parts[2], auth_url_parts[3], auth_url_parts[4]))
        self._local = threading.local()

    @property
    def checker(self):
        if not hasattr(self._local, 'checker'):
            self._local.checker = AAAChecker(self.host, self.url)
        return self._local.checker

    def authserver_check(self, content):
        content['host'] = self.service
        return self.checker.authserver_check(content)

    def apply(self, callback, route):
        @functools.wraps(callback)
        def inner_aaa(*args, **kwargs):
            request = bottle.request

            check = self.checks(request)

            path = bottle.request.path
            method = bottle.request.method
            is_collection_request = path.endswith('/')

            if not check:
                if (check.content and is_collection_request and
                        method in ('GET', 'HEAD')):
                    if not any('*' in path for path in check.raw):
                        return bottle.HTTPError(203, check.raw)
                    # The request is a collection and the central
                    # returned a list of authorized paths.
                else:
                    raise self.reject('Access Denied')

            resp = callback(*args, **kwargs)
            if method == 'GET' and is_collection_request and check.content:
                permissions = check.content
                allowed_paths = permissions.filter_paths(self.service, resp)
                self.logger.debug('Filtered %s/%s urls',
                                  len(allowed_paths), len(resp))
                if isinstance(resp, list):
                    return list(allowed_paths)
                elif isinstance(resp, dict):
                    return dict((k, resp[k]) for k in resp if k in allowed_paths)
            return resp

            # actually run the callback
        return inner_aaa

    def checks(self, request):
        content = self.authorization_extract(request)

        # self.logger.debug(msg)
        self.host_check(content)
        c = self.authserver_check(content)
        return c


class TimeMixin(object):
    def checks(self, request):
        with Chrono() as chrono:
            r = super(TimeMixin, self).checks(request)
        bottle.response.headers['x-auth-time'] = chrono.total
        return r


class NoSecureMixin(object):

    def __init__(self, *args, **kw):
        super(NoSecureMixin, self).__init__(*args, **kw)
        self.token = self.settings.get('get_parameter', 'token')

    def authorization_extract(self, request):
        if self.token in request.GET:
            login, l, signature = request.GET[self.token].partition(':')
            if l != ':':
                raise self.reject(
                    'Incorrect NAPIX non-secure Authentication', 401)
            self.logger.debug('Not secured request')
            return {
                'method': request.method,
                'path': request.path,
                'login': login,
                'signature': signature,
                'is_secure': False
            }

        content = super(NoSecureMixin, self).authorization_extract(request)
        content['is_secure'] = True
        return content

    def host_check(self, content):
        if not content['is_secure']:
            return True
        return super(NoSecureMixin, self).host_check(content)


def get_auth_plugin(secure=False, time=False):
    bases = []
    if not secure:
        bases.append(NoSecureMixin)
    if time:
        bases.append(TimeMixin)
    bases.append(AAAPlugin)
    return type(AAAPlugin)('AAAPlugin', tuple(bases), {})
