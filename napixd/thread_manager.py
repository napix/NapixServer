#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gevent
import logging

logger = logging.getLogger( 'Napix.background')

def background( fn):
    def inner(*args, **kw):
        return run_background( fn, *args, **kw)
    return inner

def run_background( fn, *args, **kw):
    logger.info( 'Start in background')
    return gevent.spawn( fn, *args, **kw)
