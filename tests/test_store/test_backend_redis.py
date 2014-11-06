#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from tests.test_store.base import _BaseTestCounter, _BaseTestStore

try:
    from napixd.store.backends.redis import (
        RedisBackend,
        RedisHashBackend,
        RedisCounterBackend,
        RedisKeyBackend,
    )
except NotImplementedError:
    __test__ = False
    def RedisKeyBackend(x): pass
    def RedisHashBackend(x): pass
    def RedisCounterBackend(x): pass
    def RedisBackend(x): pass


class TestRedisCounter(_BaseTestCounter):
    counter_class = RedisCounterBackend({})


class TestRedisStore(_BaseTestStore):
    store_class = RedisBackend({})


class TestRedisHashStore(_BaseTestStore):
    store_class = RedisHashBackend({})
    testNotSave = unittest.expectedFailure(_BaseTestStore.testNotSave)


class TestRedisKeyStore(_BaseTestStore):
    store_class = RedisKeyBackend({})
    testNotSave = unittest.expectedFailure(_BaseTestStore.testNotSave)
