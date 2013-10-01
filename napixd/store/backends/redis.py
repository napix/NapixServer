#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import

import cPickle as pickle

try:
    import redis
except ImportError:
    raise NotImplementedError('store.redis needs redis library')

from napixd.store.backends import BaseBackend, BaseStore, Store, BaseCounter


class RedisBackend(BaseBackend):

    """
    It takes optional `host` and `port` options to
    indicate to which server it connects to.
    """

    def __init__(self, options):
        if 'prefix' in options:
            prefix = options.pop('prefix')
        else:
            prefix = self.__class__.__name__
        self.prefix = prefix

        self.redis = redis.Redis(**options)

    def get_args(self, collection):
        return (self.prefix + ':' + collection, self.redis), {}

    def get_class(self):
        return RedisStore

    def keys(self):
        return self.redis.keys(self.prefix + ':*')


class RedisStore(Store):

    """
    Store based on a key in a Redis server.

    This store takes 1 key.
    """

    def __init__(self, collection, redis):
        self.redis = redis
        try:
            data = self.redis.get(collection)
            data = pickle.loads(data) if data else {}
        except redis.ResponseError:
            data = None

        super(RedisStore, self).__init__(collection, data)

    def drop(self):
        self.data = {}
        self.redis.delete(self.collection)

    def save(self):
        self.redis.set(self.collection, pickle.dumps(self.data))


class RedisHashBackend(RedisBackend):

    def get_class(self):
        return RedisHashStore


class RedisHashStore(BaseStore):

    """
    Store based on Redis Hashes.
    Every value of the store is a value of a Redis hash.
    The values are strings

    This store takes 1 key.
    """

    def __init__(self, collection, redis):
        super(RedisHashStore, self).__init__(collection)
        self.redis = redis

    def __contains__(self, key):
        return self.redis.hexists(self.collection, key)

    def __delitem__(self, item):
        self.redis.hdel(self.collection, item)

    def __getitem__(self, item):
        value = self.redis.hget(self.collection, item)
        if value is None:
            raise KeyError(item)
        return value

    def __len__(self):
        return self.redis.hlen(self.collection)

    def __setitem__(self, item, value):
        return self.redis.hset(self.collection, item, value)

    def keys(self):
        return self.redis.hkeys(self.collection)

    def values(self):
        return self.redis.hval(self.collection)

    def update(self, other_dict):
        self.redis.hmset(self.collection, other_dict)

    def items(self):
        return self.redis.hgetall(self.collection).items()

    def __eq__(self, other):
        if isinstance(other, RedisHashStore):
            return self.collection == other.collection
        else:
            return super(RedisHashStore, self).__eq__(other)

    def incr(self, key, incr=1):
        return self.redis.hincrby(self.collection, key, incr)

    def drop(self):
        self.redis.delete(self.collection)


class RedisKeyBackend(RedisBackend):

    def get_class(self):
        return RedisKeyStore


class RedisKeyStore(BaseStore):

    """
    Store based on Redis keys
    Every value of the store is a value of a Redis key.
    The values are strings.

    This store takes as many keys as values in the store.
    """

    def __init__(self, collection, redis):
        super(RedisKeyStore, self).__init__(collection)
        self.redis = redis

    def keys(self):
        # length of the collection key + length of separator
        prefix = len(self.collection) + 1
        return [x[prefix:] for x in self.redis.keys(self._all_keys())]

    def _make_key(self, key):
        return '{0}:{1}'.format(self.collection, key)

    def _all_keys(self):
        return '{0}:{1}'.format(self.collection, '*')

    def __contains__(self, key):
        return self.redis.exists(self._make_key(key))

    def __delitem__(self, item):
        self.redis.delete(self._make_key(item))

    def __getitem__(self, item):
        value = self.redis.get(self._make_key(item))
        if value is None:
            raise KeyError(item)
        return value

    def __setitem__(self, item, value):
        return self.redis.set(self._make_key(item), value)

    def update(self, other_dict):
        self.redis.mset(self.collection, other_dict)

    def __eq__(self, other):
        if isinstance(other, RedisHashStore):
            return self.collection == other.collection
        else:
            return super(RedisHashStore, self).__eq__(other)

    def incr(self, key, incr=1):
        return self.redis.incr(self._make_key(key), incr)

    def drop(self):
        for x in self.keys():
            del self[x]
        self.redis.delete(self.collection)


class RedisCounterBackend(RedisBackend):

    def get_class(self):
        return RedisCounter


class RedisCounter(BaseCounter):
    """
    A :class:`napixd.store.Counter` on a Redis server.

    This counter takes as many key as there is counters.
    """

    def __init__(self, name, redis):
        self.redis = redis
        self.name = name

    @property
    def value(self):
        return int(self.redis.get(self.name))

    def increment(self, by=1):
        return self.redis.incr(self.name, by)

    def reset(self, to=0):
        return int(self.redis.getset(self.name, 0) or 0)
