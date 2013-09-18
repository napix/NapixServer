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
    Use the `REQUEST_URI` to generate `PATH_INFO` to avoid problems with
    URL encoding.
    """

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        environ['PATH_INFO'] = urlparse.urlparse(environ['REQUEST_URI']).path
        return self.application(environ, start_response)


class CORSMiddleware(object):
    """
    Reply to OPTIONS requests emitted by browsers
    to check for Cross Origin Requests
    """

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'OPTIONS':
            start_response('200 OK', [
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods',
                 'GET, POST, PUT, CREATE, DELETE, OPTIONS'),
                ('Access-Control-Allow-Headers',
                 'Authorization, Content-Type'),
            ])
            return []
        return self.application(environ, start_response)


class LoggerMiddleware(object):
    def __init__(self, application):
        self.application = application
        self.logger = logging.getLogger('Napix.requests')

    def __call__(self, environ, orig_start_response):
        size = 0
        status = ''

        def start_response(orig_status, headers):
            global status
            status = orig_status
            orig_start_response(status, headers)

        with Chrono() as chrono:
            for x in self.application(environ, start_response):
                size += len(x)
                yield x

        self.logger.info('%s - - [%s] "%s %s" %s %s %s',
                         environ.get('REMOTE_ADDR', '-'),
                         datetime.datetime.now().replace(microsecond=0),
                         environ['REQUEST_METHOD'],
                         environ['PATH_INFO'],
                         status.split(' ')[0],
                         size,
                         chrono.total
                         )
