#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Limit the requests launched by users.
"""

import functools

import bottle

from napixd.store import Counter


class RateLimitingPlugin(object):
    """
    Limit the number of requests made by users.

    The *conf* parameter is a :class:`napixd.conf.Conf` instance
    with the parameters of the rate limit.

    Requests denied because of the rate limit will be responded
    by a 429 status code.
    """
    name = 'rate_limit'
    api = 2

    def __init__(self, conf):
        self.conf = conf

    def apply(self, callback, route):
        @functools.wraps(callback)
        def inner_rate_limit(*args, **kwargs):
            if not self.is_under_limit():
                raise bottle.HTTPError(429, 'You exceeded your quota')
            return callback(*args, **kwargs)
        return inner_rate_limit

    def is_under_limit(self):
        return True


class ConcurrentLimiter(object):
    name = 'concurrent_limit'
    api = 2

    def __init__(self, max=2):
        self.max = max

    def apply(self, callback, route):
        @functools.wraps(callback)
        def inner_concurrent_limiter(*args, **kw):
            with self.get_counter() as concurrent:
                if concurrent > self.max:
                    raise bottle.HTTPError(429, 'Too many concurrent connections')
                return callback(*args, **kw)

    def get_counter(self):
        return Counter(bottle.request.environ['REMOTE_ADDR'])
