#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from redis import Redis
except ImportError:
    def Redis(*args, **kw):
        raise NotImplementedError('The redis lib is not installed')


class cached_property(object):
    def __init__(self, fn):
        self.fn = fn
        self.__doc__ = fn.__doc__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        v = instance.__dict__[self.fn.__name__] = self.fn(instance)
        return v


class ConnectionFactory(object):
    def __init__(self, default_conf_source, connection_class=None):
        self._con_class = connection_class or Redis
        self.default_conf = default_conf_source

    @cached_property
    def default_port(self):
        return self.default_conf.get('port', 6379, type=int)

    @cached_property
    def default_host(self):
        return self.default_conf.get('host', 'localhost', type=unicode)

    @cached_property
    def default_db(self):
        return self.default_conf.get('database', 2, type=int)

    def __call__(self, conf):
        if 'host' in conf:
            host = conf.get('host', type=unicode)
            port = conf.get('port', 6379, type=int)
        else:
            host = self.default_host
            port = self.default_port
        database = conf.get('database', self.default_db, type=int)

        return self._con_class(host=host, port=port, db=database)
