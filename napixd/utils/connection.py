#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools

try:
    from redis import Redis, WatchError
except ImportError:
    class WatchError(Exception):
        pass

    def Redis(*args, **kw):
        raise NotImplementedError('The redis lib is not installed')


__all__ = [
    'ConnectionFactory',
    'transaction',
]


class cached_property(object):
    def __init__(self, fn):
        self.fn = fn
        self.__doc__ = fn.__doc__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        v = instance.__dict__[self.fn.__name__] = self.fn(instance)
        return v


class transaction(object):
    """
    A redis transaction decorator.

    It decorates a function that takes at least a :class:`redis.client.Pipeline`.
    The function can use this pipe to do redis queries and commands. The return
    value of the function is the return value of the decorated function, unless
    it returned the pipe object, in this case, the result of
    :meth:`redis.client.Pipeline.execute` is forwarded.

    The decorator takes a :class:`redis.Redis` instance as its first argument
    and uses it to create a :class:`redis.client.Pipeline`.

    Examples:

    .. code-block:: python

        def decrement_and_disappear(connection, key, index):
            "Decrement key and removes it from index if it reaches 0"

            @transaction(connection)
            def inner(pipe, key, index):
                pipe.watch(key, index)
                value = pipe.incr(key, by=-1)
                if value > 0:
                    return

                pipe.multi()
                pipe.srem(index, key)

            inner()

    .. warning::

        The decorated function may be called several times, if a :exc:`WatchError`
        happens during the execution of the pipeline.

        You **should avoid** side-effects in the callback.
    """
    def __init__(self, con):
        self._con = con

    def __call__(self, fn):
        return functools.partial(self.call, fn, self._con.pipeline())

    def call(self, fn, pipeline, *args, **kw):
        with pipeline as pipe:
            while True:
                try:
                    function_return = fn(pipe, *args, **kw)
                    pipe_execution = pipe.execute()
                    break

                except WatchError:
                    continue

        if function_return is pipe:
            return pipe_execution
        return function_return


class ConnectionFactory(object):
    """
    A redis connection factory.

    It takes a *default_conf_source* that may defines a address, port and a
    database to a Redis instance. When the connection factory is called, it
    takes another :class:`napixd.conf.Conf` instance and it retuns an insance
    of *connection_class* with the address, port and db from the 2 configurations.

    There is 3 levels of configuration: The :class:`Conf` object passed to the
    init, the :class:`Conf` object passed to the call and a set of hard coded
    parameters resolving to the localhost address, the default Redis port (6379)
    and the database 2.

    The address and the database are defined by the first source (in order, call
    conf, init conf and hard coded) returning a non-null value. The port is
    defined by the same object as the address.
    """
    def __init__(self, default_conf_source, connection_class=None):
        self._con_class = connection_class or Redis
        self.default_conf = default_conf_source

    @cached_property
    def default_port(self):
        """
        The port defined in the init conf or the hard coded default port (6379).
        """
        return self.default_conf.get('port', 6379, type=int)

    @cached_property
    def default_host(self):
        """
        The host defined in the init conf or the hard coded localhost.
        """
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
