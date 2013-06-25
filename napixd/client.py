#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import httplib
import socket
import logging
import random
import hmac
import hashlib
import string

from time import time
from urllib import urlencode

logger = logging.getLogger('Napix.client')

letters  = string.ascii_letters+string.digits
def get_nonce():
    return ''.join([
        random.choice(letters) for x in xrange(0,64)])

def sign(msg,key):
    signature= hmac.new(key,msg,hashlib.sha256).hexdigest()
    return signature

class Client( object):
    HEADERS = {
            'Accept':'application/json',
            'Content-type':'application/json',
            }
    def __init__( self, host, credentials=None, noauth=False):
        self.host = host
        self.noauth = noauth
        self.credentials = credentials
        self.key = str( credentials.get('key'))

    def request(self, method, url, body, headers_=None):
        headers = dict( self.HEADERS)
        if headers_:
            headers.update( headers_)

        if self.noauth:
            url += '&' if '?' in url else '?'
            url += 'noauth'
        elif self.credentials:
            headers['Authorization'] = self._get_authorization( method, url)

        client = httplib.HTTPConnection(self.host)
        try:
            logger.debug('Start request %s%s', self.host, url)
            client.request( method, url,
                    body = json.dumps( body), headers = headers)
            resp = client.getresponse()
            resp.read()
            logger.debug('End request %s%s', self.host, url)
            return resp
        except socket.error:
            logger.error( 'Socket error, reconnecting')
        except Exception, e:
            logger.error( 'Request failed "%s"', repr(e))
            return None

    def _get_authorization(self,method,url):
        request = {
                'login': self.credentials['login'],
                'nonce': get_nonce(),
                'path': url,
                'host': self.host,
                'method':method,
                'timestamp':str(time())
                }
        body = urlencode(request)
        signature = sign( body, self.key)
        return '%s:%s'%( body, signature)
