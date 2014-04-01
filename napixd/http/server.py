#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A WSGI server implementation
"""

import time
import logging
import json

from napixd.http.router.router import Router
from napixd.http.request import Request, HeadersDict
from napixd.http.response import HTTPError, Response, HTTPResponse, HTTP404

logger = logging.getLogger('Napix.conversations')

__all__ = ('WSGIServer', )

block_size = 1024**2


def file_wrapper(environ, filelike):
    if 'wsgi.file_wrapper' in environ:
        return environ['wsgi.file_wrapper'](filelike, block_size)
    else:
        return iter(lambda: filelike.read(block_size), '')


class WSGIServer(object):
    def __init__(self, pprint=False):
        self._router = r = Router()
        self._routers = [r]
        self._pprint = 4 if pprint else None

    def __call__(self, environ, start_response):
        environ['napixd.request'] = request = Request(environ)
        try:
            resp = self.handle(request)
        except HTTPError as error:
            resp = error

        resp = self.cast(request, resp)
        headers = resp.headers
        headers['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
        headers['Server'] = 'napixd'

        start_response(resp.status_line, headers.items())
        return resp.body

    def __repr__(self):
        rep = []
        for router in self._routers:
            rep.append(repr(router))
        return '\n----\n'.join(rep)

    def handle(self, request):
        callback = self.resolve(request.path)
        if callback is None:
            return HTTP404()
        return callback(request)

    def resolve(self, target):
        """
        Resolve the route at target.

        The first router having a match is used.
        """
        for router in reversed(self._routers):
            resolved = router.resolve(target)
            if resolved is not None:
                return resolved

    @property
    def router(self):
        return self._router

    def route(self, url, callback, **kw):
        return self._router.route(url, callback, **kw)

    def unroute(self, url, all=False):
        return self._router.unroute(url, all=all)

    def push(self, router=None):
        """
        Add a new router at the end of the stack.

        If *router* is ``None``, a new :class:`router.Router` is created.

        The router added to the stack is returned.
        """
        if router is None:
            router = Router()
        self._routers.append(router)
        return router

    def cast(self, request, response):
        if isinstance(response, Response):
            return HTTPResponse(200, response.headers, response)
        elif isinstance(response, (HTTPError, HTTPResponse)):
            status = response.status
            body = response.body
            headers = response.headers
        else:
            status = 200
            headers = HeadersDict()
            body = response

        if request.method == 'HEAD':
            body = None
            headers['Content-Length'] = 0

        content_type = headers.get('Content-Type', '')
        content_length = headers.get('Content-Length', None)

        if isinstance(body, basestring):
            if not content_type:
                content_type = 'text/plain'
            if isinstance(body, unicode):
                content_type += '; charset=utf-8'
                body = body.encode('utf-8')
        elif hasattr(body, 'read'):
            body = file_wrapper(request.environ, body)
        elif body is not None:
            content_type = 'application/json'
            body = json.dumps(body, indent=self._pprint)
        else:
            content_type = ''
            body = []

        if isinstance(body, str):
            content_length = len(body)
            body = [body]

        headers.setdefault('Content-Type', content_type)
        if content_length is not None:
            headers.setdefault('Content-Length', content_length)
        return HTTPResponse(status, headers, body)
