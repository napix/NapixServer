#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Limit the requests launched by users.
"""

import time
import logging

from napixd.store import Counter
from napixd.utils.connection import ConnectionFactory, transaction
from napixd.http.response import HTTPError, HTTPResponse
from napixd.conf.lazy import LazyConf

logger = logging.getLogger('Napix.ratelimit')


connection_factory = ConnectionFactory(LazyConf('redis'))


class RequestEnvironCriteria(object):
    def __init__(self, parameter):
        self._paramater = parameter

    def __call__(self, request):
        return request.environ.get(self._paramater)


class LimiterPlugin(object):
    def __init__(self, criteria, excludes):
        self._criteria = criteria
        self._excludes = frozenset(excludes)

    def get_criteria(self, request):
        criteria = self._criteria(request)
        if criteria in self._excludes:
            return None
        return criteria


class RateLimiterPlugin(LimiterPlugin):
    """
    Limits the number of requests made by users to *max* during *timespan*.

    When a request is denied, a 429 status response is returned.
    """

    @classmethod
    def from_settings(cls, settings, criteria):
        max = settings.get('max', type=int)
        timespan = settings.get('timespan', type=int)
        con = connection_factory(settings.get('connection'))
        excludes = settings.get_list('excludes')
        logger.info('Ratelimiting to %s/%ss via %s', max, timespan, con)
        return cls(max, timespan, con, criteria, excludes)

    def __init__(self, max, timespan, con, criteria, excludes):
        super(RateLimiterPlugin, self).__init__(criteria, excludes)
        self._max = max
        self._timespan = timespan
        self._con = con

    def __call__(self, callback, request):
        """
        :X-RateLimit-Limit:
            <number of request>/<time unit>
            the current rate limit for this API key
        :X-RateLimit-Used:
            the number of method calls used on this API key this timespan
        :X-RateLimit-Remaining:
            the estimated number of remaining calls allowed by this API key this minute
        """

        criteria = self.get_criteria(request)
        if criteria is None:
            return callback(request)

        used = self.get_rate_used(criteria)

        headers = {
            'x-ratelimit-limit': '{0}/{1}s'.format(self._max, self._timespan),
            'x-ratelimit-used': used,
            'x-ratelimit-remaining': max(self._max - used, 0),
        }

        if used >= self._max:
            logger.warning('Rejecting request of %s, quota maxed', criteria)
            return HTTPResponse(429, headers, 'You exceeded your quota')

        return HTTPResponse(headers, callback(request))

    def get_rate_used(self, criteria):
        key = 'rate_limit:{0}'.format(criteria)
        period_end = time.time()
        period_start = period_end - self._timespan

        @transaction(self._con)
        def run(pipe):
            pipe.watch(key)
            count = pipe.zcount(key, period_start, period_end)

            if count >= self._max:
                return self._max

            pipe.multi()
            pipe.zadd(key, period_end, period_end)
            pipe.expireat(key, int(period_end + self._timespan))
            return count

        count = run()
        return count


class ConcurrentLimiterPlugin(RateLimiterPlugin):
    def __init__(self, max=2):
        self.max = max

    def __call__(self, callback, request):
        with self.get_counter(request) as concurrent:
            if concurrent > self.max:
                raise HTTPError(429, 'Too many concurrent connections')
        return callback(request)

    def get_counter(self, request):
        return Counter(self.get_criteria(request))
