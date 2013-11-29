#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Limit the requests launched by users.
"""

from napixd.store import Counter
from napixd.http.response import HTTPError


class RateLimitingPlugin(object):
    """
    Limit the number of requests made by users.

    The *conf* parameter is a :class:`napixd.conf.Conf` instance
    with the parameters of the rate limit.

    Requests denied because of the rate limit will be responded
    by a 429 status code.
    """

    def __init__(self, conf):
        self.conf = conf

    def __call__(self, callback, request):
        if not self.is_under_limit():
            raise HTTPError(429, 'You exceeded your quota')
        return callback(request)

    def is_under_limit(self):
        return True


class ConcurrentLimiter(object):
    def __init__(self, max=2):
        self.max = max

    def __call__(self, callback, request):
        with self.get_counter(request) as concurrent:
            if concurrent > self.max:
                raise HTTPError(429, 'Too many concurrent connections')
        return callback(request)

    def get_counter(self, request):
        return Counter(request.environ['REMOTE_ADDR'])
