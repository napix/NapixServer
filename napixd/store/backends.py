#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import collections
import cPickle as pickle
from ..conf import Conf

class BaseStore( collections.MutableMapping):
    def __init__( self, data):
        self.data = data or {}
    def __getitem__( self, key):
        return self.data[key]
    def __setitem__( self, key, value):
        self.data[key] = value
    def __delitem__( self, key, value):
        self.data[key] = value
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

class FileStore( BaseStore ):
    PATH =  '/var/lib/napix'
    def __init__( self, collection, path = None ):
        path = path != None and path or self.get_path()
        self.file_path = os.path.join( path , collection)
        if not os.path.isdir( path):
            os.makedirs( path, 0700)
        try:
            data = pickle.load( open(self.file_path, 'r'))
        except IOError:
            data = {}
        super( FileStore, self).__init__( data )

    def drop( self):
        super( FileStore, self).drop()
        if os.path.isfile(self.file_path):
            os.unlink(self.file_path)

    def save(self):
        pickle.dump( self.data, open( self.file_path, 'w'))

    def get_path(self):
        return Conf.get_default().get( 'Napix.storage.file.directory') or self.PATH
try:
    import redis
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

except ImportError:
    pass
