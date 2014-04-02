#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.chrono import Chrono
from napixd.http.response import HTTPResponse


class TimePlugin(object):
    """
    Plugin for :mod:`napixd.http` that times the callback and sends the time
    spent in a header *header_name*.
    """

    def __init__(self, header_name):
        self.header_name = header_name

    def __call__(self, callback, request):
        with Chrono() as chrono:
            resp = callback(request)

        return HTTPResponse({self.header_name: chrono.total}, resp)
