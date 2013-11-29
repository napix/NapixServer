#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gevent
import sys


class DebugTracer(object):
    def __init__(self, out=None):
        self.hub = gevent.get_hub()
        self.is_in_the_hub = None
        self.out = out or sys.stderr

    def format(self, from_, to):
        return '\033[95m{0} -> {1}\033[0m\n'.format(
            self.format_gl(from_), self.format_gl(to))

    def format_gl(self, greenlet):
        if greenlet is self.hub:
            return 'hub'

        if not hasattr(greenlet, '_run'):
            return 'MAIN'

        runable = greenlet._run
        return getattr(runable, '__name__', str(runable))

    def __call__(self, what, who):
        if what != 'switch':
            return

        from_, to = who

        if to is self.hub:
            self.is_in_the_hub = from_
            return

        if from_ is self.hub:
            if self.is_in_the_hub is not None:
                from_ = self.is_in_the_hub
                self.is_in_the_hub = None
            else:
                from_ = self.hub

        self.out.write(self.format(from_, to))

def settrace():
    gevent.get_hub().settrace(DebugTracer())
