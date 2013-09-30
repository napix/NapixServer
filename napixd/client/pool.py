#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import gevent

from napixd.client.gevent import Client
from napixd.client.client import coerce_authenticator


class ClientPool(object):
    """
    A class that handles multiples clients
    and forward request.

    *authenticator* is a authenticator as given to :class:`napixd.client.gevent.Client`.
    *simultaneous* is the maximum number of simultaneous requests launched on the same host.

    The requests are made with :meth:`request` one by one.

    If all the responses matters, the :meth:`wait` method will block
    until they all finished.
    Else the :meth:`wait_unordered` will yield responses as they arrives,
    without order guarantee of order.

    In both case, the response is the :class:`napix.connection.Response` object
    or the :class:`napix.exceptions.HTTPError` exception if it have been raised.
    """
    def __init__(self, authenticator, simultaneous=2):
        self.authenticator = coerce_authenticator(authenticator)
        self.simultaneous = simultaneous
        self._clients = {}
        self._pool = []

    def request(self, host, *args, **kw):
        """
        request(self, host, method, uri, body, headers)

        Launches a request on the *host* and returns a :class:`gevent.Greenlet`
        See :meth:`napixd.client.client.Client.request`
        """
        if host in self._clients:
            client = self._clients[host]
        else:
            client = self._clients[host] = Client(
                host, self.authenticator, simultaneous=self.simultaneous)

        greenlet = gevent.spawn(client.request, *args, **kw)
        self._pool.append(greenlet)
        return greenlet

    def _finished(self, greenlet):
        return greenlet.value if greenlet.successful() else greenlet.exception

    def wait_unordered(self, count=-1, timeout=None):
        """
        Yields the response of the requests in the order they ended.

        If *count* is a positive integer, yields at most *count* responses.
        If *timeout* is specified, this method will block at most *timeout* seconds.
        """
        count = int(count)
        self._pool, pool = [], self._pool
        with gevent.Timeout(timeout):
            for greenlet in gevent.iwait(pool):
                yield self._finished(greenlet)
                count -= 1
                if count == 0:
                    break

    def __iter__(self):
        # copy self._pool and renew it.
        self._pool, pool = [], self._pool
        for greenlet in pool:
            greenlet.join()
            yield self._finished(greenlet)

    def wait(self):
        """
        Returns the list of all current requests when they finish.
        """
        return list(self)
