#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

class FakeAuthChecker(object):
    def __init__( self, response, testcase):
        self.testcase = testcase
        self.resp =response
    def authserver_check(self, whatever):
        self.testcase.assertEqual(whatever['path'], '/test')
        return self.resp == 200

class FakeCheckerFactory(object):
    def __init__(self, resp, testcase):
        self.testcase = testcase
        self.resp = resp
    def __call__(self, host, url):
        self.testcase.assertEqual( host, 'auth.napix.local')
        self.testcase.assertEqual( url, '/auth/authorization/')
        return FakeAuthChecker( self.resp, self.testcase)

class FakeHTTPClientFactory(object):
    def __init__(self, resp, testcase):
        self.testcase = testcase
        self.resp = resp

    def __call__(self, host):
        self.testcase.assertEqual( host, 'auth.napix.local')
        return FakeHTTPClient( self.resp, self.testcase )

class FakeHTTPClient( object):
    def __init__(self, resp, testcase):
        self.testcase = testcase
        self.resp = resp

    def getresponse(self):
        return FakeHTTPResponse( self.resp)
    def request( self, method, url, body, headers):
        self.testcase.assertEqual( method, 'POST')
        self.testcase.assertEqual( url, '/auth/authorization/')

class FakeHTTPResponse( object):
    def __init__(self, status):
        self.status = status
    def read(self):
        pass

class FakeHTTPErrorClient( object):
    def __init__(self, host):
        pass
    def request(self, method, url, body, headers):
        raise socket.error('[Errno 111] connection refused')
