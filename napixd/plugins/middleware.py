#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Various WSGI compatible middlewares.
"""

import urlparse
import logging
import datetime
from napixd.chrono import Chrono


class PathInfoMiddleware(object):
    """
    Use *key* to generate `PATH_INFO` to avoid problems with URL
    encoding.
    """

    def __init__(self, application, key='REQUEST_URI'):
        self.application = application
        self._key = key

    def __call__(self, environ, start_response):
        environ['PATH_INFO'] = urlparse.urlparse(environ[self._key]).path
        return self.application(environ, start_response)


class CORSMiddleware(object):
    """
    Reply to OPTIONS requests emitted by browsers to check for Cross Origin
    Requests.
    """

    def __init__(self, application, config):
        self.application = application
        exposed_headers = config.get('exposed_headers', None, type=list)

        if exposed_headers:
            self.exposed_headers = u', '.join(exposed_headers).encode('latin9')
        else:
            self.exposed_headers = 'Location, Content-Type'

        if config.get('origins'):
            self.allowed_origins = u', '.join(config.get('origins', type=list))
        else:
            self.allowed_origins = '*'

    def __call__(self, environ, orig_start_response):
        if environ['REQUEST_METHOD'] == 'OPTIONS':
            orig_start_response('200 OK', [
                ('Access-Control-Allow-Origin', self.allowed_origins),
                ('Access-Control-Allow-Methods',
                 'GET, POST, PUT, CREATE, DELETE, OPTIONS'),
                ('Access-Control-Allow-Headers',
                 'Authorization, Content-Type'),
            ])
            return []

        if 'HTTP_ORIGIN' in environ:
            def start_response(status, headers):
                headers = list(headers)
                headers.append(('Access-Control-Expose-Headers', self.exposed_headers))
                headers.append(('Access-Control-Allow-Origin', self.allowed_origins))
                orig_start_response(status, headers)
        else:
            start_response = orig_start_response

        return self.application(environ, start_response)


class LoggedRequest(object):
    """
    Objects returned by :class:`LoggerMiddleware`.

    Keeps the info to log.
    """
    logger = logging.getLogger('Napix.requests')

    def __init__(self, start_response, application, environ):
        self._start_response = start_response
        self.environ = environ
        self.chrono = Chrono()

        with self.chrono:
            self.response = application(self.environ, self.start_response)

    def start_response(self, status, headers):
        self.status = status
        self._start_response(status, headers)
        del self._start_response

    @property
    def username(self):
        return self.environ.get('napixd.auth.username', '-')

    @property
    def request_line(self):
        request_line = self.environ['PATH_INFO']
        if self.environ.get('QUERY_STRING'):
            request_line += '?' + self.environ['QUERY_STRING']
        return request_line

    def __iter__(self):
        size = 0
        with Chrono() as transfert:
            for x in self.response:
                size += len(x)
                yield x

        total_time = (transfert.total + self.chrono.total) * 1000

        self.logger.info('%s - %s [%s] "%s %s" %s %s %.2fms',
                         self.environ.get('REMOTE_ADDR', '-'),
                         self.username,
                         datetime.datetime.now().replace(microsecond=0),
                         self.environ['REQUEST_METHOD'],
                         self.request_line,
                         self.status.split(' ')[0],
                         size,
                         total_time,
                         )


def LoggerMiddleware(application):
    """
    Middleware that logs requests, in the combined log format
    with the body's size and the time.
    """
    def inner_logger(environ, start_response):
        return LoggedRequest(start_response, application, environ)
    return inner_logger


class HTTPHostMiddleware(object):
    """
    WSGI Middleware that checks the host againt a list of authorized hosts.
    """
    def __init__(self, hosts, application):
        self.hosts = frozenset(hosts)
        self.application = application

    def __call__(self, environ, start_response):
        if environ.get('HTTP_HOST') not in self.hosts:
            response = 'Bad host'
            start_response('400 Bad Request', [
                ('Content-Length', str(len(response))),
                ('Content-Type', 'text/plain'),
            ])
            return [response]

        return self.application(environ, start_response)
