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
    def inner(*args, **kw):
        return run_background(fn, *args, **kw)
    return inner


def run_background(fn, *args, **kw):
    logger.info('Start in background')
    if with_gevent:
        return gevent.spawn(fn, *args, **kw)
    else:
        thread = threading.Thread(target=fn, args=args, kwargs=kw)
        thread.daemon = True
        thread.start()
        return thread
