#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time


class Chrono(object):

    def __init__(self):
        self.start = None
        self.end = None

    def __repr__(self):
        if self.start is None:
            return '<Chrono unstarted>'
        elif self.end is None:
            return '<Chrono for {0:.2g}>'.format(time.time() - self.start)
        return '<Chrono {0:.2g}>'.format(self.total)

    @property
    def total(self):
        return self.end - self.start

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.end = time.time()
