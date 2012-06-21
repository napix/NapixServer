#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Lock

try:
    import redis
except ImportError:
    redis = None

from ..conf import Conf


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

if redis:
    class RedisCounter(object):
        def get_default_options( self):
            return Conf.get_default().get( 'Napix.storage.redis') or {}
        def __init__( self, name, options=None):
            options = options != None and options or self.get_default_options()
            self.redis = redis.Redis( **options )
            self.name = name

        @property
        def value(self):
            return int( self.redis.get(self.name))

        def increment( self, by=1):
            return self.redis.incr( self.name, by)

        def reset(self, to=0):
            return int( self.redis.getset( self.name, 0) )

