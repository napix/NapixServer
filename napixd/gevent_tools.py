#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import time
import logging

import gevent
import gevent.greenlet
import gevent.pool
import gevent.hub

logger = logging.getLogger( 'Napix.gevent')

class Chrono(object):
    def __init__(self):
        self.start = None
        self.end = None
    def __repr__(self):
        if self.start is None:
            return '<Chrono unstarted>'
        elif self.end is None:
            return '<Chrono for %.2g>' % ( time.time() - self.start)
        return '<Chrono  %.2g>' % ( self.total)

    @property
    def total(self):
        return self.end - self.start

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.end = time.time()


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

class Pool( gevent.pool.Pool):
    greenlet_class = Greenlet

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
            with Chrono() as timing:
                proc = Greenlet.spawn( callback, *args, **kw)
                resp = proc.get()
            resp.headers['x-total-time'] = timing.total
            resp.headers['x-running-time'] = proc.get_running_time()

            return resp
        return inner_gevent_time_header


