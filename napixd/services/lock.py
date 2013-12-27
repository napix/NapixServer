#!/usr/bin/env python
# -*- coding: utf-8 -*-


from napixd.conf.lazy import LazyConf
from napixd.utils.lock import Lock
from napixd.utils.connection import ConnectionFactory

__all__ = [
    'LockFactory',
]

cf = ConnectionFactory(LazyConf('lock'))


class LockFactory(object):
    def __init__(self, connection_factory=None, lock_class=Lock):
        self._lock_cls = lock_class
        self._con_fac = (connection_factory
                         if connection_factory is not None
                         else cf)

    def __call__(self, conf):
        name = conf.get('name', type=unicode)
        con = self._con_fac(conf)
        return self._lock_cls(name, con)
