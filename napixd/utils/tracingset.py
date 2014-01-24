#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections


class TracingSet(collections.Set):
    def __init__(self, values):
        self.values = frozenset(values)
        self.checked = set()

    @property
    def unchecked(self):
        return self.values.difference(self.checked).difference(
            'no' + key for key in self.checked)

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

    def __contains__(self, key):
        self.checked.add(key)
        return key in self.values
