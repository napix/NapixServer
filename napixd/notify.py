#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import logging
import socket
import httplib
import urlparse


from .thread_manager import background
from .conf import Conf

logger = logging.getLogger('Napix.notifications')

class Notifier(object):
    def __init__( self, app, client=None, delay=None ):
        self.app = app
        self._alive = True


        post_url = Conf.get_default( 'Napix.notify.url')
        post_url_bits = urlparse.urlsplit( post_url )
        self.post_url = post_url_bits.path
        self.client_class = client or httplib.HTTPConnection
        self.client_args = ( post_url_bits.hostname, post_url_bits.port)
        self.connect()

        self.put_url = None

        self.delay = delay or Conf.get_default('Napix.notify.delay') or 300
        logger.info( 'Notify on %s every %ss', self.post_url, self.delay)
        if self.delay < 1:
            logger.warning( 'Notification delay is below 1s, the minimum rate is 1s')

    def connect(self):
        self.client = self.client_class( *self.client_args)

    @background(name='notify_thread')
    def start(self):
        for x in range(3):
            if self.send_first_notification():
                break
            time.sleep(2)
        else:
            logger.error('Did not succeed to notifications')
            return
        logger.info('Running loop')
        self.loop()


    def loop( self):
        count = 0
        while self._alive:
            time.sleep(1)
            if count > self.delay:
                count = 0
                self.send_notification()
                continue
            count += 1

    def stop(self):
        self._alive = False

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
        headers = { 'Accept':'application/json',
                'Content-type':'application/json', }
        try:
            self.client.request( method, url + '?authok',
                    body = json.dumps( self._get_request_content()), headers=headers)
            resp = self.client.getresponse()
            resp.read()
            return resp
        except socket.error:
            logger.error( 'Socket error, reconnecting')
            self.connect()
        except Exception, e:
            logger.error( 'Update failed "%s"', repr(e))
            return None

    def _get_request_content(self):
        return {
                'host' : Conf.get_default('Napix.auth.service') or socket.gethostname(),
                'managers' : list(self.app.root_urls),
                }
