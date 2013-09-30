#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import collections

from napix.connection import Connection, HTTPError
from napix.authenticators import LoginAuthenticator

logger = logging.getLogger('Napix.Client')


def coerce_authenticator(authenticator):
    """
    Ensure that the authenticator is a suitable object.
    """
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
    Standart Client.

    *host* is the destination server name

    *authenticator* is either a :class:`dict`
    (or a :class:`~napixd.conf.Conf` instance)
    with keys *login* and *key* used with a
    :class:`napix.authenticators.LoginAuthenticator`,
    or a callable, such as a :mod:`built-in authenticator<napixd.authenticators>`.
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
