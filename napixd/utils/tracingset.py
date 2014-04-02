#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections


class TracingSet(collections.Set):
    """
    :class:`set` like class that keeps a track of the values that have been
    checked with *in*. Keys starting with *no* are considered checked if a
    key without the prefix is checked.

    >>> t = TracingSet('abc')
    >>> 'a' in t
    True
    >>> 'd' in t
    False
    >>> t.unchecked
    set(['b', 'c'])
    """
    def __init__(self, values):
        self.values = frozenset(values)
        self.checked = set()

    @property
    def unchecked(self):
        """
        The set of keys that have not been checked.
        """
        return self.values.difference(self.checked).difference(
            'no' + key for key in self.checked)

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

    def __contains__(self, key):
        self.checked.add(key)
        return key in self.values
