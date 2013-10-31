#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A Router for Web URLs.

A router handles a set of routes, represented as a tree
of :class:`~napixd.http.router.step.RouterStep` and a list of filters

The filters are simple callables that can alter the request or the response,
or even the call to a view.

Each filter is called with the callback and the request.
The filter can alter the request or the response.
It sends the call forward by calling the callback with the request.

.. code-block:: python

    def lock_filter(callback, request):
        lock.acquire()
        try:
            return callback(request)
        finally:
            lock.release()


    router.add_filter(lock_filter)

"""

from napixd.http.router.step import RouterStep, URLTarget


class FilterResolved(object):
    """
    A callback that applies a filter.
    """
    def __init__(self, callback, filter):
        self._callback = callback
        self._filter = filter

    def __call__(self, request):
        return self._filter(self._callback, request)

    def __eq__(self, other):
        return (isinstance(other, FilterResolved) and
                other._callback == self._callback and
                other._filter == self._filter)


class Router(object):
    """
    A router with filters.

    When a route is resolved, the filters are applied on the callback
    """
    def __init__(self):
        self._filters = []
        self._router = RouterStep('')

    def add_filter(self, filter):
        """
        Add a *filter* to the list of filters.

        The filters added last are applied first.
        """
        self._filters.append(filter)

    def route(self, path, callback, catchall=False):
        """
        Register a route with the given *callback*.
        """
        if not callable(callback):
            raise ValueError('callback is not callable')
        return self._router.route(URLTarget(path), callback, catchall)

    def unroute(self, url, all=False):
        """
        Remove the route at *url*.

        When *all* is True, all the routes under the target are removed,
        else only the matching callback is removed.

        When a route does not exist it is silently ignored.
        """
        self._router.unroute(URLTarget(url), all=all)

    def resolve(self, path):
        """
        Resolve the *target* url.

        If the router finds a route matching, it returns an instance
        of :class:`FilterResolved` with the filters.
        Else it returns ``None``.
        """
        resolved = self._router.resolve(URLTarget(path))
        if not resolved:
            return resolved

        for filter in reversed(self._filters):
            resolved = FilterResolved(resolved, filter)

        return resolved
