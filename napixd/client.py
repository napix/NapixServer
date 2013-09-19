#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from napix.connection import Connection, HTTPError
from napix.authenticators import LoginAuthentifier, AnonAuthentifier


logger = logging.getLogger('Napix.Client')


class Client(object):

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
