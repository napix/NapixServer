#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Lock

def LocalBackend(opts):
    return LocalCounter

class LocalCounter(object):
    def __init__( self, name):
        self.name = name
        self.value = 0
        self.lock= Lock()

    def increment( self, by=1):
        with self.lock:
            self.value += by
            return self.value

    def reset( self, to=0):
        with self.lock:
            old_value = self.value
            self.value = to
            return old_value

