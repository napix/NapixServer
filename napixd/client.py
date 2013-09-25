#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Client lib of napix.

It uses the :mod:`napix` to do requests.
"""

import logging

from napix.connection import Connection, HTTPError
from napix.authenticators import LoginAuthentifier, AnonAuthentifier


logger = logging.getLogger('Napix.Client')


class Client(object):
    """
    Helper class for :class:`napix.connection.Connection` and
    :class:`napix.authenticators.AnonAuthentifier` and
    :class:`napix.authenticators.LoginAuthentifier`.

    *host* is the destination host and *credentials* a dict containing
    ``login`` and ``key``.

    If *noauth* is true, a :class:`napix.authenticators.AnonAuthentifier`
    is used.
    """

    def __init__(self, host, credentials=None, noauth=False):
        self.host = host
        if noauth:
            authenticator = AnonAuthentifier()
        else:
            authenticator = LoginAuthentifier(
                credentials['login'], credentials['key'])

        self.conn = Connection(host, authenticator, follow=False)

    def request(self, method, url, body='', headers=None):
        try:
            resp, content = self.conn.request(method, url, body, headers)
        except HTTPError as e:
            logger.info('Error on %s: %s', self.host, e)
            raise
        return resp
