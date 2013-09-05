#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.chrono import Chrono


class TimePlugin(object):
    name = 'time_plugin'
    api = 2

    def __init__(self, header_name):
        self.header_name = header_name

    def apply(self, callback, route):
        def inner_time(*args, **kw):
            with Chrono() as chrono:
                resp = callback(*args, **kw)
            resp.headers[self.header_name] = chrono.total
            return resp
        return inner_time
