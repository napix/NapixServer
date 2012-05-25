#!/usr/bin/env python
# -*- coding: utf-8 -*-

class _Request(object):
    def __init__(self,url,**data):
        self.GET={}
        self.url = url
        self.method = self.__class__.__name__
        self.data = data
        self.path = url
        self.environ = {'PATH_INFO':self.url,
                'REQUEST_METHOD':self.method,
                'SERVER_PROTOCOL' : 'HTTP/1.1'
                }
    def get(self,value):
        return self.environ.get(value)

class POST(_Request) : pass
class PUT(_Request) : pass
class GET(_Request) : pass
class DELETE(_Request) : pass
