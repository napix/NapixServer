#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urlparse
import urllib


class PathInfoMiddleware(object):

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        environ['PATH_INFO'] = urlparse.urlparse(environ['REQUEST_URI']).path
        return self.application(environ, start_response)


class CORSMiddleware(object):

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'OPTIONS':
            start_response('200 OK', [
                ('Access-Control-Allow-Origin',  '*'),
                ('Access-Control-Allow-Methods',
                 'GET, POST, PUT, CREATE, DELETE, OPTIONS'),
                ('Access-Control-Allow-Headers',
                 'Authorization, Content-Type'),
            ])
            return []
        return self.application(environ, start_response)
