#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

from napixd.client.client import Client as BaseClient
from gevent.coros import Semaphore


class Client(BaseClient):
    """
    A client made to be used with :mod:`gevent`.

    The *simultaneous* argument is the maximum number of concurrent requests
    made by this instance.
    """
    def __init__(self, host, authenticator, simultaneous=2):
        super(Client, self).__init__(host, authenticator)
        self.semaphore = Semaphore(simultaneous)

    def request(self, method, url, body='', headers=None):
        with self.semaphore:
            return super(Client, self).request(method, url, body, headers)
