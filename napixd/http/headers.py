#!/usr/bin/env python
# -*- coding: utf-8 -*-


import collections


class HeadersDict(collections.MutableMapping):
    """
    A mapping class suitable as HTTP headers.

    All the keys are compared lower-case and with all the ``_``
    replaced by ``-``.
    """
    def __init__(self, headers=None):
        self.headers = {}
        if headers:
            self.update(headers)

    def __setitem__(self, key, value):
        if isinstance(value, unicode):
            value = value.encode('iso-8859-1')
        else:
            value = str(value)
        self.headers[key.replace('_', '-').lower()] = value

    def __getitem__(self, key):
        return self.headers[key.replace('_', '-').lower()]

    def __delitem__(self, key):
        del self.headers[key.replace('_', '-').lower()]

    def __iter__(self):
        return iter(self.headers)

    def __len__(self):
        return len(self.headers)

    def __contains__(self, key):
        return key.replace('_', '-').lower() in self.headers

    def __repr__(self):
        return repr(self.headers)
