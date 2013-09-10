#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napix.connection import Connection, HTTPError
from napix.authenticators import LoginAuthentifier, AnonAuthentifier


class Client(object):
    def __init__(self, host, credentials=None, noauth=False):
        if noauth:
            authenticator = AnonAuthentifier()
        else:
            authenticator = LoginAuthentifier(
                credentials['login'], credentials['key'])

        self.conn = Connection(host, authenticator, follow=False)

    def request(self, method, url, body='', headers=None):
        resp, content = self.conn.request(method, url, body, headers)
        return resp
