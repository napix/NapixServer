#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Lock
from napixd.store.backends import BaseBackend, BaseCounter


class LocalValues(object):
    def __init__(self):
        self.values = {}
        self.lock = Lock()

    def __enter__(self):
        self.lock.acquire()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.lock.release()

    def __getitem__(self, name):
        return self.values.get(name, 0)

    def __setitem__(self, name, value):
        if value == 0:
            if name in self.values:
                del self.values[name]
        else:
            self.values[name] = value


class LocalBackend(BaseBackend):
    """
    Returns :class:`LocalCounter` instances.
    """
    def __init__(self):
        self.values = LocalValues()

    def dump(self):
        return {}

    def load(self, values):
        pass

    def drop(self):
        pass

    def get_class(self):
        return LocalCounter

    def get_args(self, collection):
        return (collection, self.values), {}


class LocalCounter(BaseCounter):
    """
    An in-memory counter.
    """

    def __init__(self, name, localvalues):
        self.name = name
        self.values = localvalues

    @property
    def value(self):
        return self.values[self.name]

    def increment(self, by=1):
        with self.values:
            self.values[self.name] += by
            return self.value

    def reset(self, to=0):
        with self.values:
            old_value = self.values[self.name]
            self.values[self.name] = 0
            return old_value
