#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Notify the Napix Directory
--------------------------

This module implements the notify protocol between a Napix Server
and a directory.
"""

try:
    from gevent import sleep
except ImportError:
    from time import sleep

import logging
import socket
import urlparse

from napixd.client import Client, HTTPError
from napixd.thread_manager import background
from napixd.conf import Conf
from napixd.guid import uid

logger = logging.getLogger('Napix.notifications')


class Notifier(object):
    """
    The object handling the notification process.

    It notifies at regular intervals a server.
    The delay and the target server are defined in *conf*

    The *app* is the source of the **applications** sent to the directory.
    """

    def __init__(self, app, conf, service_name):
        self.app = app
        self.service_name = service_name

        self.directory = post_url = conf.get('url')
        post_url_bits = urlparse.urlsplit(post_url)
        self.post_url = post_url_bits.path

        credentials = conf.get('credentials')
        self.client = Client(post_url_bits.netloc, credentials)
        self.put_url = None

        self.delay = conf.get('delay') or 300
        logger.info('Notify on %s%s as %s every %ss', post_url_bits.netloc,
                    self.post_url, credentials.get('login', '<anon>'), self.delay)
        if self.delay < 1:
            logger.warning(
                'Notification delay is below 1s, the minimum rate is 1s')
            self.delay = 1

    def start(self):
        if self.post_url is None:
            return
        self.job = self._start()

    @background
    def _start(self):
        self.run()

    def run(self):
        for x in range(3):
            if self.send_first_notification():
                break
            sleep(10)
        else:
            logger.error('Did not succeed to notifications')
            return

        logger.info('Running loop')
        while True:
            sleep(self.delay)
            self.send_notification()

    def send_first_notification(self):
        """
        Sends the first notification, a POST request.

        The POST request retrieves the url at which the values
        are PUT by :meth:`send_notification` afterwards.
        """
        try:
            resp = self.send_request('POST', self.post_url)
        except HTTPError, err:
            logger.warning('Got %s', err)
            return False

        if resp.status == 201:
            self.put_url = resp.getheader('location')
            logger.info('Now putting at %s', self.put_url)
            return True

    def send_notification(self):
        """
        Sends the next notifications through PUT requests
        """
        logger.info('updating %s', self.put_url)
        self.send_request('PUT', self.put_url)

    def send_request(self, method, url):
        return self.client.request(method, url, body={
            'uid': str(uid),
            'host': Conf.get_default('Napix.auth.service') or socket.gethostname(),
            'service': self.service_name,
            'description': Conf.get_default('Napix.description') or '',
            'managers': list(self.app.root_urls),
        })
