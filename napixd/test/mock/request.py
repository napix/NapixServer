#!/usr/bin/env python
# -*- coding: utf-8 -*-

class _Request(object):
    def __init__(self,**data):
        self.GET={}
        self.method = self.__class__.__name__
        self.data = data

class POST(_Request) : pass
class PUT(_Request) : pass
class GET(_Request) : pass
class DELETE(_Request) : pass
