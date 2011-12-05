#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Response(object):
    def __init__(self,status):
        self.status = status
        self.headers = {}
        self.content = ''
    def __iter__(self):
        return iter([''])

class MockHTTPClient(object):
    def __init__(self,status):
        self.status = status

    def request(self,uri,method,headers=None,body=None):
        return Response(self.status), ''
