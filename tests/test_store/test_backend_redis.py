#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
from tests.test_store.base import _BaseTestCounter, _BaseTestStore

try:
    from napixd.store.backends import redis
except NotImplementedError:
    @unittest2.skip('Missing "redis" dependency')
    class TestRedisBackend(unittest2.TestCase):
        pass
else:
    class TestRedisCounter(_BaseTestCounter):
        counter_class = redis.RedisCounterBackend({})

    class TestRedisStore(_BaseTestStore):
        store_class = redis.RedisBackend({})

    class TestRedisHashStore(_BaseTestStore):
        store_class = redis.RedisHashBackend({})
        testNotSave = unittest2.expectedFailure(_BaseTestStore.testNotSave)

    class TestRedisKeyStore(_BaseTestStore):
        store_class = redis.RedisKeyBackend({})
        testNotSave = unittest2.expectedFailure(_BaseTestStore.testNotSave)
