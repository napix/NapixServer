#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import time
import logging
import bottle

import gevent
import gevent.greenlet
import gevent.wsgi
import gevent.hub

from napixd.chrono import Chrono

logger = logging.getLogger( 'Napix.gevent')


class Greenlet(gevent.greenlet.Greenlet):
    def __init__(self, *args, **kw):
        super( Greenlet, self).__init__(*args, **kw)
        self._times = []

    def add_time(self):
        self._times.append( time.time())

    def get_running_intervals(self):
        i = iter(self._times)
        now = time.time()
        for t in i:
            yield t, next(i, now)

    def get_running_time(self):
        return sum( end-start for start, end in self.get_running_intervals())

class Tracer(object):
    def __init__( self):
        self.last = None
    def trace(self, what, who):
        if what != 'switch':
            return
        from_, to = who
        if self.last is not None:
            self.last.add_time()
            self.last = None

        if isinstance( to, Greenlet):
            to.add_time()
            self.last = to

    def set_trace(self):
        logger.info( 'Set trace')
        hub = gevent.hub.get_hub()
        self.old_trace = hub.gettrace()
        gevent.hub.get_hub().settrace(self.trace)

    def unset_trace(self):
        logger.info( 'Unset trace')
        hub = gevent.hub.get_hub()
        hub.settrace( self.old_trace)

class AddGeventTimeHeader(object):
    name = 'gevent_time_header'
    api = 2
    def __init__(self):
        self.tracer = Tracer()
        self.tracer.set_trace()

    def apply(self, callback, route):
        @functools.wraps(callback)
        def inner_gevent_time_header(*args, **kw):
            import bottle
            before = bottle._lctx.__dict__
            def bs(cb,*args,**kw):
                bottle._lctx.__dict__.update( before)
                return cb( *args, **kw)

            with Chrono() as timing:
                proc = Greenlet.spawn( bs, callback, *args, **kw)
                resp = proc.get()
            resp.headers['x-total-time'] = timing.total
            resp.headers['x-running-time'] = proc.get_running_time()
            return resp
        return inner_gevent_time_header

class WSGIHandler(gevent.pywsgi.WSGIHandler):
    def get_environ(self):
        env = super( WSGIHandler, self).get_environ()
        path, x, query = self.path.partition('?')
        env['PATH_INFO'] = path
        return env


class GeventServer(bottle.ServerAdapter):
    def run(self, handler):
        log = None if self.quiet else 'default'
        gevent.pywsgi.WSGIServer(
                (self.host, self.port),
                handler,
                handler_class = WSGIHandler,
                log=log).serve_forever()


