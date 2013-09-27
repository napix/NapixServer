#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Client lib of napix.

It uses the :mod:`napix` to do requests.
"""

import logging
import collections

from napix.connection import Connection, HTTPError
from napix.authenticators import LoginAuthenticator


__all__ = ('Client', )

logger = logging.getLogger('Napix.Client')


def coerce_authenticator(authenticator):
    if isinstance(authenticator, collections.Mapping):
        try:
            authenticator = LoginAuthenticator(
                authenticator['login'],
                authenticator['key'])
        except KeyError:
            pass

    if not callable(authenticator):
        raise ValueError('Authenticator must be a dict {login, key} or a callable')
    return authenticator


class Client(object):
    """
    Helper class for :class:`napix.connection.Connection` and
    :class:`napix.authenticators.LoginAuthenticator`.

    *host* is the destination host and *credentials* a dict containing
    ``login`` and ``key``.
    """

    def __init__(self, host, authenticator):
        self.host = host
        authenticator = coerce_authenticator(authenticator)
        self.conn = Connection(host, authenticator, follow=False)

    def request(self, method, url, body='', headers=None):
        try:
            resp, content = self.conn.request(method, url, body, headers)
        except HTTPError as e:
            logger.info('Error on %s: %s', self.host, e)
            raise
        return resp
