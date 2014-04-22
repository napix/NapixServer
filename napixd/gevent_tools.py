#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tools used with :mod:`gevent`.

A feature implemented by :class:`Tracer` allows to keep track of the time spent
executing Python in an observed greenlet, excluding the IO and the other greenlets.

The other feature is :class:`GeventServer` witch acts as a WSGI server and
overrides the value of the environ key ``PATH_INFO`` to undo all unescaping.
"""

import time
import logging

import gevent
import gevent.greenlet
import gevent.wsgi
import gevent.hub

from napixd.chrono import Chrono

from napixd.http import Adapter
from napixd.http.response import HTTPResponse

logger = logging.getLogger('Napix.gevent')


class Greenlet(gevent.greenlet.Greenlet):
    """
    A greenlet subclass that tracks the time it is running
    """
    def __init__(self, *args, **kw):
        super(Greenlet, self).__init__(*args, **kw)
        self._times = []

    def add_time(self):
        """
        Add a timestamp.
        """
        self._times.append(time.time())

    def get_running_intervals(self):
        """
        Return the pair (begin, end) of the times
        this instance has been running.
        """
        i = iter(self._times)
        now = time.time()
        for t in i:
            yield t, next(i, now)

    def get_running_time(self):
        """
        Return the time in seconds during witch this greenlet has been running.
        """
        return sum(end - start for start, end in self.get_running_intervals())


class Tracer(object):
    """
    A object tracing the activity of greenlets.

    .. attribute:: last

        The last :class:`Greenlet` wich have been running
    """
    def __init__(self):
        self.last = None

    def trace(self, what, who):
        """
        Callback executed for every switch of greenlet
        """
        if what != 'switch':
            return
        from_, to = who
        if self.last is not None:
            self.last.add_time()
            self.last = None

        if isinstance(to, Greenlet):
            to.add_time()
            self.last = to

    def set_trace(self):
        """
        Plug the tracer into gevent.
        """
        logger.info('Set trace')
        hub = gevent.hub.get_hub()
        self.old_trace = hub.gettrace()
        gevent.hub.get_hub().settrace(self.trace)

    def unset_trace(self):
        """
        Unplug the tracer
        """
        logger.info('Unset trace')
        hub = gevent.hub.get_hub()
        hub.settrace(self.old_trace)


class AddGeventTimeHeader(object):
    """
    A :mod:`napixd.http` plugin used to transfert the results of the time spent
    by the :class:`gevent.greenlet` to the users by the HTTP headers.
    """

    def __init__(self):
        self.tracer = Tracer()
        self.tracer.set_trace()

    def __call__(self, callback, request):
        with Chrono() as timing:
            proc = Greenlet.spawn(callback, request)
            resp = proc.get()

        return HTTPResponse({
            'x-total-time': timing.total,
            'x-running-time': proc.get_running_time()
        }, resp)


class WSGIHandler(gevent.pywsgi.WSGIHandler):
    """
    A WSGI handler used by :class:`GeventServer`

    It overrides the value of PATH_INFO to avoid unescaping.
    """
    def get_environ(self):
        env = super(WSGIHandler, self).get_environ()
        path, x, query = self.path.partition('?')
        env['PATH_INFO'] = path
        return env


class GeventServer(Adapter):
    """
    This object installs the :class:`WSGIHandler` as its handler.
    """
    def run(self, handler):
        log = None if self.quiet else 'default'
        gevent.pywsgi.WSGIServer(
            (self.host, self.port),
            handler,
            handler_class=WSGIHandler,
            log=log).serve_forever()
