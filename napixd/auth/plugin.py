#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from napixd.http.response import HTTPError, HTTPResponse
from napixd.chrono import Chrono


logger = logging.getLogger('Napix.auth')


class AAAPlugin(object):
    """
    Authentication, Authorization and Accounting plugins
    """

    def __init__(self, sources, providers, timed=True):
        self._timed = timed
        self._sources = sources
        self._providers = providers

    def __call__(self, callback, request):
        try:
            return self.authorize(callback, request)
        except HTTPError as e:
            logger.info('Rejecting request of %s: %s %s',
                        request.environ.get('REMOTE_ADDR', 'unknow'),
                        e.status, e.body)
            raise

    def extract(self, request):
        for source in self._sources:
            extract = source(request)
            if extract is not None:
                logger.debug('Extracting from %s', source.__class__.__name__)
                return extract
        else:
            raise HTTPError(401, 'You need to sign your request')

    def authenticate(self, request, content):
        for provider in self._providers:
            result = provider(request, content)
            if result is not None:
                logger.debug('Authorisation provided by %s', provider.__class__.__name__)
                return result
        else:
            raise HTTPError(403, 'No source')

    def authorize(self, callback, request):
        content = self.extract(request)
        with Chrono() as chrono:
            check = self.authenticate(request, content)

        logger.debug('Authenticate took %s', chrono.total)

        if not check:
            raise HTTPError(403, 'Access Denied')

        resp = callback(request)
        if callable(check):
            resp = check(resp)

        if self._timed:
            return HTTPResponse({'x-auth-time': chrono.total}, resp)
        return resp
