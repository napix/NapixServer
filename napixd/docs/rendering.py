#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections


class Context(collections.MutableMapping):
    def __init__(self, previous=None):
        self.current = {}
        self.previous = previous if previous is not None else {}

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        return iter(self.keys())

    def keys(self):
        keys = set(self.current.keys())
        keys.update(self.previous.keys())
        return keys

    def __getitem__(self, key):
        if key in self.current:
            return self.current[key]
        value = self.previous[key]

        if isinstance(value, list):
            value = self[key] = list(value)
        elif isinstance(value, dict):
            value = self[key] = dict(value)

        return value

    def __setitem__(self, key, value):
        self.current[key] = value

    def __delitem__(self, key):
        if key in self.current:
            del self.current[key]

    def __nonzero__(self):
        return bool(self.current) or bool(self.previous)

    def __contains__(self, key):
        return key in self.current or key in self.previous


class DocStrings(object):
    def __init__(self, value):
        self.value = value

    def __getattr__(self, name):
        attr = getattr(self.value, name, None)
        return attr and DocString(attr)


def DocString(method):
    return (getattr(method, '__doc__', None) or '').strip()
