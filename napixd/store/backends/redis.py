#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import

import cPickle as pickle

try:
    import redis
except ImportError:
    raise NotImplementedError, 'store.redis needs redis library'

from napixd.store.backends import BaseStore
from napixd.conf import Conf

class BaseRedisStore( BaseStore ):
    def get_default_options( self):
        return Conf.get_default().get( 'Napix.storage.redis') or {}

    def __init__( self, collection, options= None):
        options = options != None and options or self.get_default_options()
        self.redis = redis.Redis( **options )
        self.collection = collection

    def drop(self):
        super(BaseRedisStore, self).drop()
        self.redis.delete(self.collection)

class RedisStore( BaseRedisStore ):
    def __init__(self, collection, options=None):
        super(RedisStore, self).__init__(collection, options)
        try:
            data = self.redis.get( collection)
            self.data = pickle.loads( data ) if data else {}
        except redis.ResponseError:
            pass

    def save( self):
        self.redis.set( self.collection, pickle.dumps( self.data ))

class RedisHashStore(BaseRedisStore):
    def __contains__( self, key):
        return self.redis.hexists( self.collection, key)

    def __delitem__(self, item):
        self.redis.hdel( self.collection, item)

    def __getitem__(self, item):
        value = self.redis.hget( self.collection, item)
        if value is None:
            raise KeyError, item
        return value

    def __len__( self):
        return self.redis.hlen( self.collection)

    def __setitem__(self, item, value):
        return self.redis.hset( self.collection, item, value)

    def keys(self):
        return self.redis.hkeys(self.collection)

    def values( self):
        return self.redis.hval( self.collection)

    def update( self, other_dict):
        self.redis.hmset(self.collection, other_dict)

    def items( self):
        return self.redis.hgetall(self.collection).items()

    def __eq__(self, other):
        if isinstance( other, RedisHashStore):
            return self.collection == other.collection
        else:
            return super( RedisHashStore, self).__eq__( other)

    def incr(self, key, incr=1):
        return self.redis.hincrby( self.collection, key, incr)

class RedisKeyStore(BaseRedisStore):
    def _make_key(self, key):
        return '{0}:{1}'.format( self.collection, key)
    def _all_keys( self):
        return '{0}:{1}'.format( self.collection, '*')

    def __contains__( self, key):
        return self.redis.exists( self._make_key( key))

    def __delitem__(self, item):
        self.redis.delete( self._make_key( item))

    def __getitem__(self, item):
        value = self.redis.get( self._make_key( item))
        if value is None:
            raise KeyError, item
        return value

    def __iter__(self):
        return iter(self.keys())

    def __len__( self):
        return len( self.keys())

    def __setitem__(self, item, value):
        return self.redis.set( self._make_key( item), value)

    def keys(self):
        return [ x.partition(':')[2] for x in self.redis.keys( self._all_keys()) ]

    def update( self, other_dict):
        self.redis.mset(self.collection, other_dict)

    def __eq__(self, other):
        if isinstance( other, RedisHashStore):
            return self.collection == other.collection
        else:
            return super( RedisHashStore, self).__eq__( other)

    def incr(self, key, incr=1):
        return self.redis.incr( self._make_key( key), incr)

    def drop(self):
        for x in self.keys():
            del self[x]

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

