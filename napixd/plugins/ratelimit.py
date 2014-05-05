#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Limit the requests launched by users.
"""

import time
import logging

from napixd.store import Counter
from napixd.utils.connection import ConnectionFactory
from napixd.http.response import HTTPError
from napixd.conf.lazy import LazyConf

logger = logging.getLogger('Napix.ratelimit')


connection_factory = ConnectionFactory(LazyConf('redis'))


class RateLimitingPlugin(object):
    """
    Limits the number of requests made by users to *max* during *timespan*.

    When a request is denied, a 429 status response is returned.
    """

    @classmethod
    def from_settings(cls, settings):
        max = settings.get('max', type=int)
        timespan = settings.get('timespan', type=int)
        con = connection_factory(settings.get('connection'))
        logger.info('Ratelimiting to %s/%ss via %s', max, timespan, con)
        return cls(max, timespan, con)

    def __init__(self, max, timespan, con):
        self._max = max
        self._timespan = timespan
        self._con = con

    def __call__(self, callback, request):
        criteria = self.get_criteria(request)
        if not self.is_under_limit(criteria):
            logger.warning('Rejecting request of %s, quota maxed', criteria)
            return HTTPError(429, 'You exceeded your quota')

        return callback(request)

    def get_criteria(self, request):
        return request.environ.get('REMOTE_ADDR', '?')

    def is_under_limit(self, criteria):
        key = 'rate_limit:{0}'.format(criteria)
        period_end = time.time()
        period_start = period_end - self._timespan

        with self._con.pipeline() as pipe:
            pipe.zcount(key, period_start, period_end)
            pipe.zadd(key, period_end, period_end)
            pipe.expireat(key, int(period_end + self._timespan))
            count, add, xat = pipe.execute()

        return count < self._max


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
