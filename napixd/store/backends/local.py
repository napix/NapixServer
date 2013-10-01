#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Lock
from napixd.store.backends import BaseBackend, BaseCounter


class LocalBackend(BaseBackend):
    """
    Returns :class:`LocalCounter` instances.
    """
    def dump(self):
        return {}

    def load(self, values):
        pass

    def drop(self):
        pass

    def __call__(self):
        return LocalCounter


class LocalCounter(BaseCounter):
    """
    An in-memory counter.
    """

    def __init__(self, name):
        self.name = name
        self.value = 0
        self.lock = Lock()

    def increment(self, by=1):
        with self.lock:
            self.value += by
            return self.value

    def reset(self, to=0):
        with self.lock:
            old_value = self.value
            self.value = to
            return old_value
