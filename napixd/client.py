#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Client lib of napix.

It uses the :mod:`napix` to do requests.
"""

import logging

from napix.connection import Connection, HTTPError
from napix.authenticators import LoginAuthenticator, AnonAuthenticator


logger = logging.getLogger('Napix.Client')


class Client(object):
    """
    Helper class for :class:`napix.connection.Connection` and
    :class:`napix.authenticators.AnonAuthenticator` and
    :class:`napix.authenticators.LoginAuthenticator`.

    *host* is the destination host and *credentials* a dict containing
    ``login`` and ``key``.
    """

    def __init__(self, host, credentials=None, authentifier=None):
        self.host = host
        authenticator = LoginAuthenticator(
            credentials['login'], credentials['key'])

        self.conn = Connection(host, authenticator, follow=False)

    def request(self, method, url, body='', headers=None):
        try:
            resp, content = self.conn.request(method, url, body, headers)
        except HTTPError as e:
            logger.info('Error on %s: %s', self.host, e)
            raise
        return resp
