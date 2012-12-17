#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import gevent


def background( fn):
    @functools.wraps(fn)
    def decorated(*args, **kw):
        return gevent.spawn( fn, *args, **kw)
    return decorated


