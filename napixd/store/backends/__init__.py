#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections

"""
=====================
Store implementations
=====================

Implementations of :class:`StoreBackend`.

Asynchronous implementations
============================

Synchronous implementations needs the user to call :meth:`.save<StoreBackend.save>`
on the store after a modification has been made.

Synchronous implementations
===========================

Asynchronous implementations directly commit the modifications to the underlying persistance support.
Setting a value from a place and getting it after returns the same data,
whatever the order of the creation of the stores.

"""

class BaseStore( collections.MutableMapping):
    def __init__( self, data):
        self.data = data or {}
    def __getitem__( self, key):
        return self.data[key]
    def __setitem__( self, key, value):
        self.data[key] = value
    def __delitem__( self, key):
        del self.data[key]
    def __iter__(self):
        return iter(self.keys())
    def __len__( self):
        return len( self.keys())
    def keys(self):
        return self.data.keys()
    def incr(self, key, incr=1):
        self[key] += 1
        return self[key]
    def drop(self):
        self.data = {}
    def save(self):
        pass

