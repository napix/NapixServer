#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The napix Configuration class.

The Napix Configuration is a :class:`collections.MutableMapping`.
Keys are accessible by their name, or their path.
Their path are composed of each descendant joined by a ``.``.

The defautl configuration is loaded from a JSON file
:file:`HOME/conf/settings.json`

"""


import __builtin__
import logging
import os.path
import collections

logger = logging.getLogger('Napix.conf')

# So that it's overridable in the tests
open = open

_sentinel = object()


class ConfLoader(object):
    """
    Load the configuration from the default file.

    If the configuration file does not exists,
    a new configuration file is created.
    """
    def __init__(self, paths, filename):
        self.filename = filename
        self.paths = [os.path.join(path, filename) for path in paths]

    def get_default_conf(self):
        return os.path.join(os.path.dirname(__file__), self.filename)

    def load_file(self, path):
        logger.info('Using %s configuration file', path)
        handle = open(path, 'rb')
        try:
            return self.parse_file(handle)
        finally:
            handle.close()

    def parse_file(self, handle):
        raise NotImplementedError()

    def copy_default_conf(self):
        default_conf = self.get_default_conf()
        logger.warning('Did not find any configuration, trying default conf from %s',
                       default_conf)
        with open(default_conf, 'r') as handle:
            conf = self.parse_file(handle)

        for path in self.paths:
            try:
                logger.info('Try to write default conf to %s', path)
                with open(path, 'w') as destination:
                    with open(default_conf, 'r') as source:
                        destination.write(source.read())
            except IOError:
                logger.warning('Failed to write conf in %s', path)
            else:
                logger.info('Conf written to %s', path)
                break
        else:
            logger.error('Cannot write defaulf conf')

        return conf

    def __call__(self):
        conf = None
        paths = iter(self.paths)
        for path in paths:
            if os.path.isfile(path):
                conf = self.load_file(path)
                break
        else:
            try:
                conf = self.copy_default_conf()
            except IOError:
                logger.error('Did not find any configuration at all')
                conf = {}

        return Conf(conf)


class Conf(collections.Mapping):

    """
    Configuration Object

    The configuration object are dict like values.

    An access can span multiple keys

    .. code-block:: python

        c = Conf({ 'a': { 'b' : 1 }})
        c.get('a.b) == 1
    """
    _default = None

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
        return len(self.data)

    @classmethod
    def get_default(cls, value=None):
        """
        Get a value on the default conf instance.
        """
        if cls._default is None:
            raise ValueError('Configuration is not loaded')
        if value is None:
            return cls._default
        else:
            return cls._default.get(value)

    @classmethod
    def set_default(cls, instance):
        if instance is None:
            cls._default = None
            return None

        if not isinstance(instance, cls):
            raise TypeError('value must be an instance of the class')
        cls._default = instance
        return instance

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
        return bool(self.data)

    def __eq__(self, other):
        return (isinstance(other, collections.Mapping) and
                other.keys() == self.keys() and
                other.values() == self.values())

    def get(self, section_id, default_value=_sentinel, type=None):
        """
        Return the value pointed at **section_id**.

        If the key does not exist, **default_value** is returned.
        If *default_value* is left by default, an empty :class:`Conf`
        instance is returned.
        """
        try:
            value = self[section_id]
        except (KeyError, ValueError):
            if default_value is not _sentinel:
                return default_value
            if type is not None:
                raise
            return Conf()

        if type and not isinstance(value, type):
            raise TypeError('{key} has not the required type "{required}" but is a "{actual}"'.format(
                key=section_id, required=type, actual=__builtin__.type(value).__name__))

        if isinstance(value, dict):
            return Conf(value)
        return value
