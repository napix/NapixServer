#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from napixd.http.response import HTTPError, HTTPResponse
from napixd.chrono import Chrono


logger = logging.getLogger('Napix.auth')


class AAAPlugin(object):
    """
    Authentication, Authorization and Accounting plugins

    It takes a list of :ref:`auth.sources` and a list of :ref:`auth.providers`.
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
        """
        Uses the :ref:`auth.sources` to retrieve informations from the request.

        It returns the first non-``None`` result of a :ref:`source<auth.sources>`.
        When all sources returns ``None``, it raises a 401.
        """
        for source in self._sources:
            extract = source(request)
            if extract is not None:
                logger.debug('Extracting from %s', source.__class__.__name__)
                return extract
        else:
            raise HTTPError(401, 'You need to sign your request')

    def authenticate(self, request, content):
        """
        Authenticates the *request* with the **providers**.

        It returns the first non-``None`` result of a provider.
        When all providers returns None, it raises a 403.
        """
        for provider in self._providers:
            result = provider(request, content)
            if result is not None:
                logger.debug('Authorisation provided by %s', provider.__class__.__name__)
                return result
        else:
            raise HTTPError(403, 'No source')

    def authorize(self, callback, request):
        """
        Calls :meth:`authenticate` and the *callback*

        If :meth:`authenticate` returns a callable, it will call it
        with the result of the callback.

        When the *timed* option is enabled, the time spend in :meth:`authenticate`
        will be calculated and returned in the **x-auth-time** header.
        """
        content = self.extract(request)
        if 'login' in content:
            request.environ['napixd.auth.username'] = content['login']

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
