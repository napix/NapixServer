#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import gevent
import logging

logger = logging.getLogger( 'Napix.background')

def background( fn):
    return functools.partial( run_background, fn)

def run_background( fn, *args, **kw):
    logger.info( 'Start in background')
    return gevent.spawn( fn, *args, **kw)
