#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import wsgiref.simple_server


class WSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler, object):
    def get_environ(self):
        environ = super(WSGIRequestHandler, self).get_environ()
        if '?' in self.path:
            path, qs = self.path.split('?')
        else:
            path = self.path
        environ['PATH_INFO'] = path
        return environ


class QuietWSGIRequestHandler(WSGIRequestHandler):
    def log_request(self, *args, **kw):
        pass
