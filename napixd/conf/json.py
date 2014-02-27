#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json
from cStringIO import StringIO

from napixd import conf


class ConfFactory(object):
    def get_filename(self):
        return 'settings.json'

    def parse_string(self, string):
        return self.parse_file(StringIO(string))

    def parse_file(self, handle):
        try:
            return Conf(json.load(handle))
        except ValueError as e:
            raise ValueError(
                'Configuration file contains a bad JSON object ({0})'.format(e))


class CompatConfFactory(ConfFactory):
    def parse_file(self, handle):
        return CompatConf(super(CompatConfFactory, self).parse_file(handle))


class Conf(conf.BaseConf):

    """
    Configuration Object

    The configuration object are dict like values.

    An access can span multiple keys

    .. code-block:: python

        c = Conf({ 'a': { 'b' : 1 }})
        c.get('a.b) == 1
    """

    def __init__(self, data=None):
        self.data = dict(data) if data else {}

    def __repr__(self):
        return repr(self.data)

    def __iter__(self):
        return (key for key in self.data if not key.startswith('#'))

    def iteritems(self):
        return ((key, value)
                for key, value in self.data.items()
                if not key.startswith('#'))

    def __len__(self):
        return sum(0 if key.startswith('#') else 1
                   for key in self.data)

    def __getitem__(self, item):
        if item in self.data:
            return self.data[item]
        if '.' in item:
            prefix, x, suffix = item.partition('.')
            base = self[prefix]
            if isinstance(base, dict):
                return Conf(base)[suffix]
        raise KeyError(item)

    def __contains__(self, item):
        if not self:
            return False
        if item in self.data:
            return True
        if '.' in item:
            prefix, x, suffix = item.partition('.')
            return suffix in self.get(prefix)
        return False

    def __nonzero__(self):
        return any(not key.startswith('#') for key in self.data)

    def get(self, *args, **kw):
        value = super(Conf, self).get(*args, **kw)
        if isinstance(value, dict):
            value = Conf(value)

        return value


class CompatConf(conf.BaseConf):
    def __init__(self, conf):
        self.conf = conf

    def __iter__(self):
        return iter(self.conf)

    def __len__(self):
        return len(self.conf)

    def __getattr__(self, attr):
        return getattr(self.conf, attr)

    def __getitem__(self, key):
        if key.startswith('Manager '):
            key = key[8:]
        else:
            key = 'Napix.' + key
        value = self.conf[key]
        if isinstance(value, dict):
            return Conf(value)
        return value
