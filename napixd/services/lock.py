#!/usr/bin/env python
# -*- coding: utf-8 -*-


import redis

from napixd.conf import Conf
from napixd.utils.lock import (
    Lock as OriginalLock,
    synchronized as original_synchronized
)
from napixd.managers.base import ManagerType


def get_connection(conf):
    if not isinstance(conf, Conf):
        conf = Conf(conf)

    host = conf.get('host', type=basestring)
    port = conf.get('port', type=int)
    database = conf.get('database', type=int)

    return redis.Redis(host=host, port=port, db=database)


connection = get_connection(Conf.get_default())


class Lock(OriginalLock):
    def __init__(self, name, *args, **kw):
        super(Lock, self).__init__(name, connection, *args, **kw)


def synchronized(lock):
    if not isinstance(lock, OriginalLock):
        lock = Lock(lock)

    wrapper = original_synchronized(lock)

    def inner_synchronized(fn):
        if isinstance(fn, ManagerType):
            raise NotImplementedError()
        else:
            return wrapper(fn)

    return inner_synchronized
