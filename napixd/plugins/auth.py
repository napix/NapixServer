#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import httplib
import json
import socket
import urlparse

import hmac
import hashlib

from permissions.models import Perm
from permissions.managers import PermSet

from napixd.http.response import HTTPError, HTTPResponse
from napixd.chrono import Chrono

TIMEOUT = 5


class Check(object):

    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__, self.content)


class Success(Check):

    def __init__(self, content=None):
        if content and isinstance(content, list):
            content = PermSet(Perm(p['host'], p['methods'], p['path'])
                              for p in content)
        else:
            content = None
        super(Success, self).__init__(content)

    def __nonzero__(self):
        return True


class Fail(Check):

    def __init__(self, content=None):
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
            raise HTTPError(500, 'Auth server did not respond')
        except socket.timeout as e:
            self.logger.error('Auth server timed out, %r', e)
            raise HTTPError(504, 'Auth server timeout')
        except socket.error as e:
            self.logger.error('Auth server did not respond, %r', e)
            raise HTTPError(500, 'Auth server did not respond')
        finally:
            self.http_client.close()
            self.logger.debug('Finished the request to the auth server')

        if resp.status != 200 and resp.status != 403:
            self.logger.error('Auth server responded a %s', resp.status)
            self.logger.debug('Auth server said: %s', content)
            raise HTTPError(
                500, 'Auth server responded unexpected %s code' % resp.status)

        if resp.getheader('content-type') == 'application/json':
            content = json.loads(content)

        if resp.status != 200:
            return Fail(content)

        return Success(content)


class BaseAAAPlugin(object):

    def __init__(self, conf, service_name=''):
        self.settings = conf

        hosts = self.settings.get('hosts')
        if hosts:
            if (isinstance(hosts, list) and
                    all(isinstance(h, basestring) for h in hosts)):
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
        return HTTPError(code, cause)

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

    def host_check(self, request, content):
        try:
            if self.hosts is not None and content['host'] not in self.hosts:
                raise self.reject('Bad host')
            path = request.path
            if request.query_string:
                path += '?' + request.query_string

            if content['method'] != request.method:
                raise self.reject(
                    'Bad authorization data method does not match')
            signed = content['path']
            if signed != path:
                raise self.reject('Bad authorization data path does not match')
        except KeyError, e:
            raise self.reject('Missing authentication data: %s' % e)

    def __call__(self, callback, request):
        try:
            resp = self.authorize(callback, request)
        except HTTPError as e:
            self.logger.info('Rejecting request of %s: %s %s',
                             request.environ.get('REMOTE_ADDR', 'unknow'),
                             e.status, e.body)
            raise

        return resp


class AAAPlugin(BaseAAAPlugin):

    """
    Authentication, Authorization and Accounting plugins

    FIXME : A documenter quand ce sera arreté
    """
    logger = logging.getLogger('Napix.AAA')

    def __init__(self, conf, service_name=''):
        super(AAAPlugin, self).__init__(conf, service_name=service_name)
        url = self.settings.get('auth_url')
        auth_url_parts = urlparse.urlsplit(url)
        self.logger.info('Set up authentication with %s', url)
        self.host = auth_url_parts.netloc
        self.url = urlparse.urlunsplit(
            ('', '', auth_url_parts[2], auth_url_parts[3], auth_url_parts[4]))

    def authserver_check(self, content):
        content['host'] = self.service
        checker = AAAChecker(self.host, self.url)
        return checker.authserver_check(content)

    def authorize(self, callback, request):
        check = self.checks(request)

        path = request.path
        method = request.method
        is_collection_request = path.endswith('/')

        if not check:
            if (check.content and is_collection_request and
                    method in ('GET', 'HEAD')):
                if not any('*' in path for path in check.raw):
                    return HTTPError(203, check.raw)
                # The request is a collection and the central
                # returned a list of authorized paths.
            else:
                raise self.reject('Access Denied')

        resp = callback(request)
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

    def checks(self, request):
        content = self.authorization_extract(request)

        # self.logger.debug(msg)
        self.host_check(request, content)
        c = self.authserver_check(content)
        return c


class TimeMixin(object):
    def __call__(self, callback, request):
        resp = super(TimeMixin, self).__call__(callback, request)
        return HTTPResponse({'x-auth-time': request.auth_duration}, resp)

    def checks(self, request):
        with Chrono() as chrono:
            r = super(TimeMixin, self).checks(request)

        request.auth_duration = chrono.total
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
                'msg': login,
                'is_secure': False
            }

        content = super(NoSecureMixin, self).authorization_extract(request)
        content['is_secure'] = True
        return content

    def host_check(self, request, content):
        if not content['is_secure']:
            return True
        return super(NoSecureMixin, self).host_check(request, content)


class AutonomousMixin(object):
    def __init__(self, *args, **kw):
        super(AutonomousMixin, self).__init__(*args, **kw)
        self.login = self.settings.get('login', 'local_master')
        password = self.settings.get('password', None)
        if not password:
            raise ValueError('password cannot be empty. Set Napix.auth.password')

        self.password = password.encode('utf-8')

    def authserver_check(self, content):
        if content['login'] == self.login:
            if content['signature'] == self.sign(content['msg']):
                self.logger.info('Authorize local request')
                return Success()

            return Fail()

        return super(AutonomousMixin, self).authserver_check(content)

    def sign(self, msg):
        return hmac.new(self.password, msg, hashlib.sha256).hexdigest()


def get_auth_plugin(secure=False, time=False, autonomous=False):
    bases = []
    if not secure:
        bases.append(NoSecureMixin)
    if time:
        bases.append(TimeMixin)
    if autonomous:
        bases.append(AutonomousMixin)

    bases.append(AAAPlugin)
    return type(AAAPlugin)('AAAPlugin', tuple(bases), {})
