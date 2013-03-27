#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gevent import sleep
import logging
import socket
import urlparse

from napixd.client import Client
from napixd.thread_manager import background
from napixd.conf import Conf

logger = logging.getLogger('Napix.notifications')

class Notifier(object):
    def __init__( self, app, delay=None ):
        self.app = app
        self._alive = False

        if not Conf.get_default('Napix.notify.url'):
            logger.error('Notifier has no configuration options')
            self.post_url = None
            return

        post_url = Conf.get_default( 'Napix.notify.url')
        post_url_bits = urlparse.urlsplit( post_url )
        self.post_url = post_url_bits.path

        self.client = Client( post_url_bits.netloc, Conf.get_default( 'Napix.notify.credentials'))
        self.put_url = None

        self.delay = delay or Conf.get_default('Napix.notify.delay') or 300
        logger.info( 'Notify on %s every %ss', self.post_url, self.delay)
        if self.delay < 1:
            logger.warning( 'Notification delay is below 1s, the minimum rate is 1s')
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
        resp = self.send_request(  'POST', self.post_url)
        if resp and resp.status == 201:
            self.put_url = resp.getheader('location')
            logger.info( 'Now putting at %s', self.put_url)
            return True
        elif resp is None:
            return False
        else:
            logger.warning('Got %s %s response from notification url %s',
                    resp.status, resp.reason, self.post_url)
            return False

    def send_notification(self):
        logger.info( 'updating %s', self.put_url)
        self.send_request(  'PUT', self.put_url)

    def send_request( self, method, url):
        return self.client.request( method, url,
                body ={
                    'host' : Conf.get_default('Napix.auth.service') or socket.gethostname(),
                    'description' : Conf.get_default('Napix.description') or '',
                    'managers' : list(self.app.root_urls),
                    })
