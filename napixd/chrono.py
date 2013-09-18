#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time


class Chrono(object):
    """
    A class used as a context manager to get the timing of a code section.

    >>> with Chrono() as chrono:
    ...     time.sleep(1)
    >>> print(chrono)
    <Chrono 1>
    """
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
        """
        The total time spend inside the code section in seconds.
        """
        if self.end is None:
            return time.time() - self.start
        return self.end - self.start

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.end = time.time()
