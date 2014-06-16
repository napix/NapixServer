#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import gevent
    with_gevent = True
except ImportError:
    with_gevent = False
    import threading

import logging

logger = logging.getLogger('Napix.background')


def background(fn):
    """
    Decorator that calls the decorated function with :func:`run_background`.

    The function returns a :class:`gevent.Greenlet` or a :class:`threading.Thread`.
    """
    def inner(*args, **kw):
        return run_background(fn, *args, **kw)
    return inner


def run_background(fn, *args, **kw):
    """
    Runs the function *fn* with *args* and *kw* in a separate :class:`Thread` or
    :class:`Greenlet`. Returns the Greenlet.
    """
    logger.info('Start %s in background', fn.__name__)
    if with_gevent:
        return gevent.spawn(fn, *args, **kw)
    else:
        thread = threading.Thread(target=fn, args=args, kwargs=kw)
        thread.daemon = True
        thread.start()
        return thread
