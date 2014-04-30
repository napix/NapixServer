#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Routers Steps classes.
The routers are recursive dict of :class:`RouterStep`.

Each step handles a path bit associated to a callback and
delegates to its children for all the paths under.

A :class:`RouterStep` manages the life cycle of the RouterStep under.
It creates them when a :meth:`RouterStep.route` requires it and remove them
after a call to :meth:`RouterStep.unroute` removes all the routes in a child step.
"""

import urllib

__all__ = [
    'RouterStep',
    'CatchAllRouterStep',
    'URLTarget',
    'ResolvedRequest',
    'RouteTaken',
]


class URLTarget(object):
    """
    A representation of a target URL suited for the steps.

    It follows the flow of the path bits and can record the arguments

    *target* is a string URL.

    .. attribute:: arguments

        A list of arguments.
    """
    def __init__(self, target):
        self.arguments = []
        self._target = target.split('/')
        if self._target[0] != u'':
            raise ValueError('Path does not start with a /')
        self._idx = 0
        self._len = len(self._target) - 1

    def __eq__(self, other):
        return isinstance(other, URLTarget) and self._target == other._target

    def __repr__(self):
        return 'Target {0}, args({1})'.format(
            self.remaining, ';'.join(self.arguments))

    @property
    def remaining(self):
        """The unparsed remaining of the URL"""
        return '/'.join(self._target[self._idx + 1:])

    def __iter__(self):
        return self

    def __nonzero__(self):
        return self._idx != self._len

    def next(self):
        if self:
            self._idx += 1
            return self._target[self._idx]
        else:
            raise StopIteration()

    def add_argument(self, arg):
        """
        Add an argument to the list of :attr:`arguments`.
        """
        self.arguments.append(urllib.unquote(arg).decode('utf-8'))


class RouteTaken(Exception):
    """
    The exception raised when trying to register a route already taken.
    """
    pass


class ResolvedRequest(object):
    """
    A partial of the *callback* and its *arguments*.
    """
    def __init__(self, callback, args):
        self._callback = callback
        self.args = args

    def __call__(self, request):
        return self._callback(request, *self.args)

    def __eq__(self, other):
        return (isinstance(other, ResolvedRequest) and
                other._callback == self._callback and
                other.args == self.args)


class RouterStep(object):
    """
    A path bit.

    Each :class:`RouterStep` handles the path without the '/' and delegates to
    children :class:`RouterStep` for the path.
    """
    def __init__(self):
        # _fixed, the map of the static paths token
        self._fixed = {}
        # Callback associated to this '/'
        self._callback = None

    def __repr__(self, level=0):
        paths = []
        if self._callback is not None:
            paths.append('=> {0}'.format(self._callback.__name__))
        for route, rs in self._fixed.items():
            if route == '?':
                continue

            if len(rs._fixed) == 0:
                paths.append('{0} {1}'.format(route or '/', repr(rs)))
            else:
                paths.append('{0} ->\n{1}'.format(route or '/', rs.__repr__(level=level+1)))
        if '?' in self._fixed:
            paths.append('* ->\n{0}'.format(self._fixed['?'].__repr__(level=level+1)))
        return '\n'.join(' ' * level + path for path in paths)

    def __nonzero__(self):
        #A router is truthy if it has at least a rule
        return self._callback is not None or bool(self._fixed)

    def route(self, target, callback, catchall=False):
        """
        Register a route with the given *callback*.

        *target* is an instance of :class:`URLTarget`

        The *target*  can contain either full path bits that must be equal to
        match or ``?`` to indicate a default route and save this as an argument.
        Path bits are chosen first.
        """
        dest = next(target, None)
        if dest is None:
            # <router>
            if self._callback:
                raise RouteTaken('This route is already register to {0}'.format(self._callback))
            self._callback = callback
            return self

        # <router>/<dest>
        if catchall and not target:
            if dest:
                raise ValueError('catchall URL must end with a "/"')
            if '' in self._fixed:
                raise RouteTaken('The / route is taken')
            if '?' in self._fixed:
                raise RouteTaken('Impossible to record all routes')
            router = self._fixed['?'] = CatchAllRouterStep(callback)
            return router

        if dest in self._fixed:
            router = self._fixed[dest]
        else:
            router = self._fixed[dest] = RouterStep()
        return router.route(target, callback, catchall)

    def unroute(self, target, all=False):
        """
        Remove the specified *target* route.

        *target* is an instance of :class:`URLTarget`

        When *all* is True, all the routes under the target are removed,
        else only the matching callback is removed.

        When a route does not exist it is silently ignored.
        All class:`RouterStep` under this one that have no routes anymore are removed.
        """
        dest = next(target, None)
        if dest is None:
            self._callback = None
            if all:
                self._fixed.clear()
            return self

        if dest == '' and isinstance(self._fixed.get('?'), CatchAllRouterStep):
            dest = '?'

        if dest in self._fixed:
            router = self._fixed[dest]
            router.unroute(target, all=all)
            if not router:
                del self._fixed[dest]

    def __contains__(self, target):
        dest = next(target, None)
        if dest is None:
            return self._callback is not None
        if dest in self._fixed:
            return target in self._fixed[dest]
        if (dest == '' and '?' in self._fixed and
                isinstance(self._fixed['?'], CatchAllRouterStep)):
            return True
        return False

    def resolve(self, target):
        """
        Resolve the *target* url.

        *target* is an instance of :class:`URLTarget`.

        If the router finds a route matching, it returns an instance of :class:`ResolvedRequest`
        with the callback and the arguments from the url.
        Else it returns ``None``.
        """
        dest = next(target, None)
        if dest is None:
            if self._callback is None:
                return None

            return ResolvedRequest(self._callback, target.arguments)

        if dest not in self._fixed:
            router = self._fixed.get('?')
            if router is None:
                return None

            target.add_argument(dest)
        else:
            router = self._fixed[dest]

        return router.resolve(target)


class CatchAllRouterStep(object):
    """
    A :class:`RouterStep` like class that catches all the requests under its namespace and feeds it to its callback.

    Routes cannot be added under this router.

    All the :meth:`resolve` calls returns a :class:`ResolvedRequest`.
    The callback takes the arguments of the url and as last argument,
    the remaining portion of path.
    """
    def __init__(self, callback):
        self._callback = callback

    def __contains__(self, target):
        return False

    def __nonzero__(self):
        return self._callback is not None

    def __repr__(self, level=0):
        return '{pad}** -> {0}'.format(self._callback.__name__, pad=' ' * level)

    def unroute(self, route, all):
        if route:
            #try to unroute a route inside
            return

        self._callback = None

    def route(self, target, callback, catchall=False):
        raise RouteTaken('The router catches all routes under this path')

    def resolve(self, target):
        if self._callback is None:
            return None
        args = list(target.arguments)
        last_path = args.pop()
        args.append(last_path + '/' + target.remaining if last_path else '')
        return ResolvedRequest(self._callback, args)
