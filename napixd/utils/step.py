#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import functools


class Steps(object):
    """
    A tool to manage the execution of a list of callables.

    The instances of this class are decorators for a list of callable.
    The callable are executed one after the other, not necessarily in the
    same order of their declaration.

    After running a callable an optional user specified callback *cb*
    is executed with the :class:`Steps` instance as argument.
    """
    def __init__(self, cb=None):
        self.total = 0
        self.current = 0
        self.current_fn = None
        self.stack = []
        self.cb = cb

    def __call__(self, fn):
        @functools.wraps(fn)
        def inner_step(*args, **kw):
            self.current_fn = fn
            r = fn(*args, **kw)
            self.current += 1
            self.notify_progress()
            return r

        self.stack.append(inner_step)
        self.total += 1

        return inner_step

    def notify_progress(self):
        """
        Notifies the progress.
        """
        if self.cb:
            self.cb(self)

    @property
    def progress(self):
        """
        The progress as a float between 0 and 1, 1 being the end.
        """
        return self.current / self.total
