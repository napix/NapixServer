#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import httplib
import socket
import json
import urlparse

from permissions.models import Perm
from permissions.managers import PermSet

from napixd.http.response import HTTPError


logger = logging.getLogger('Napix.AAA.Checker')

TIMEOUT = 5


class FilterFactory(object):
    def __init__(self, service):
        self.service = service

    def __call__(self, rules):
        return Filter(PermSet(Perm(p['host'], p['methods'], p['path'])
                              for p in rules).on_host(self.service))


class Filter(object):
    def __init__(self, rules):
        self.rules = rules

    def __call__(self, resp):
        allowed_paths = self.rules.filter_paths(resp)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Filtered %s/%s urls', len(allowed_paths), len(resp))

        if isinstance(resp, list):
            return list(allowed_paths)
        elif isinstance(resp, dict):
            return dict((k, resp[k]) for k in resp if k in allowed_paths)
        else:
            raise ValueError()


class ConnectionFactory(object):
    def __init__(self, host, timeout=TIMEOUT):
        self.host = host
        self.timeout = timeout

    def __call__(self):
        return httplib.HTTPConnection(self.host, timeout=self.timeout)

    def __eq__(self, other):
        return type(self) == type(other) and self.host == other.host


class CentralAuthProvider(object):
    headers = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
    }

    @classmethod
    def from_settings(cls, service, settings):
        try:
            url = settings.get('url', type=unicode)
        except TypeError:
            logger.warning('Using old parameter auth_url')
            url = settings.get('auth_url', type=unicode)
        auth_url_parts = urlparse.urlsplit(url)
        logger.info('Set up authentication with %s', url)
        host = auth_url_parts.netloc
        url = urlparse.urlunsplit(
            ('', '', auth_url_parts[2], auth_url_parts[3], auth_url_parts[4]))
        return cls(ConnectionFactory(host), url, FilterFactory(service))

    def __init__(self, connection_factory, url, filter_factory):
        self.url = url
        self.http_client_factory = connection_factory
        self.filter_factory = filter_factory

    def __call__(self, request, content):
        resp, content = self._do_request(content)

        have_filter = request.path.endswith('/') and request.method in ('GET', 'HEAD')
        if resp.status != 200:
            if not have_filter:
                # Discard Non GET/HEAD requests and requests on resources
                return False

            paths = [perm['path'] for perm in content]
            if content and not any('*' in path for path in paths):
                # Return a non-authoritative response
                raise HTTPError(203, paths)
            else:
                # Return a response that filters the content of the response
                return self.filter_factory(content)
        elif have_filter:
            return self.filter_factory(content)
        else:
            return True

    def _do_request(self, body):
        body = json.dumps(body)
        http_client = self.http_client_factory()
        try:
            logger.debug('Sending request to the auth server')
            http_client.request('POST', self.url, body=body, headers=self.headers)
            resp = http_client.getresponse()
            content = resp.read()
        except socket.gaierror, e:
            logger.error('Auth server %s not found %s', self.host, e)
            raise HTTPError(500, 'Auth server did not respond')
        except socket.timeout as e:
            logger.error('Auth server timed out, %r', e)
            raise HTTPError(504, 'Auth server timeout')
        except socket.error as e:
            logger.error('Auth server did not respond, %r', e)
            raise HTTPError(500, 'Auth server did not respond')
        finally:
            http_client.close()
            logger.debug('Finished the request to the auth server')

        if resp.status != 200 and resp.status != 403:
            logger.error('Auth server responded a %s', resp.status)
            logger.debug('Auth server said: %s', content)
            raise HTTPError(500, 'Auth server responded unexpected %s code' % resp.status)

        if resp.getheader('content-type') == 'application/json':
            content = json.loads(content)
        else:
            content = None

        return resp, content
