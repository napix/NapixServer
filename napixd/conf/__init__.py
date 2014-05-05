#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The napix Configuration class.

The Napix Configuration is a :class:`collections.MutableMapping`.
Keys are accessible by their name, or their path.
Their path are composed of each descendant joined by a ``.``.
"""


import __builtin__
import logging
import os.path
import collections

logger = logging.getLogger('Napix.conf')


_sentinel = object()


class ConfLoader(object):
    """
    Loader of configuration.

    A loader is associated with a *factory*. The factory can convert string and
    files to :class:`Conf` objects and the loader finds the files.
    If no file is found a default configuration depending from the factory
    is created at the first writable search emplacement
    """
    def __init__(self, paths, conf_factory):
        self.factory = conf_factory
        filename = conf_factory.get_filename()
        self.paths = [os.path.join(path, filename) for path in paths]

    def get_default_conf(self):
        """
        Returns the path to the default file for this factory.
        """
        return os.path.join(os.path.dirname(__file__), self.factory.get_filename())

    def load_file(self, path):
        """
        Loads a file using the factory.
        """
        logger.info('Using %s configuration file', path)
        handle = open(path, 'rb')
        try:
            return self.factory.parse_file(handle)
        except IOError:
            logger.error('Error while trying to open conf file %s', path)
            raise
        finally:
            handle.close()

    def clone_destination(self, content):
        """
        Clones the default configuration in the first writable emplacement.
        """
        for path in self.paths:
            try:
                logger.info('Try to write default conf to %s', path)
                with open(path, 'wb') as destination:
                    destination.write(content)
            except IOError:
                logger.warning('Failed to write conf in %s', path)
            else:
                logger.info('Conf written to %s', path)
                break
        else:
            logger.error('Cannot write defaulf conf')

    def copy_default_conf(self):
        """
        Writes the default configuration.
        """
        default_conf = self.get_default_conf()
        logger.warning('Did not find any configuration, trying default conf from %s',
                       default_conf)
        source = None
        try:
            source = open(default_conf, 'rb')
            conf = self.factory.parse_file(source)
            source.seek(0)
            self.clone_destination(source.read())
        except IOError:
            logger.error('Did not find any configuration at all')
            return EmptyConf()
        finally:
            if source:
                source.close()

        return conf

    def __call__(self):
        conf = None
        paths = iter(self.paths)
        for path in paths:
            if os.path.isfile(path):
                conf = self.load_file(path)
                break
        else:
            conf = self.copy_default_conf()

        return conf


class BaseConf(collections.Mapping):
    """
    Base class for configuration objects.
    """
    _default = None

    def __eq__(self, other):
        return (isinstance(other, collections.Mapping) and
                other.keys() == self.keys() and
                other.values() == self.values())

    def get(self, section_id, default_value=_sentinel, type=None):
        """
        get(section_id, [default_value], type=None)

        Return the value pointed at **section_id**.

        If the key does not exist, **default_value** is returned. If
        *default_value* is left by default, an empty :class:`Conf` instance is
        returned.

        If *type* is given, the value at *section_id* must exist and be an
        instance of *type*, else a :exc:`TypeError` is raised.  When used in
        combination with *default_value*, it is returned if there is no value
        instead of the :exc:`TypeError` but the :exc:`TypeError` is still
        raised when the value is not an instance of the *type*.
        """
        try:
            value = self[section_id]
        except KeyError:
            if default_value is not _sentinel:
                return default_value
            if type is not None:
                raise TypeError(u'The key {0} is required but does not exists'.format(section_id))
            return EmptyConf()

        if type and not isinstance(value, type):
            raise TypeError('{key} has not the required type "{required}" but is a "{actual}"'.format(
                key=section_id, required=type, actual=__builtin__.type(value).__name__))

        return value

    def get_list(self, key, default_value=_sentinel):
        """
        Returns a list of values.

        If the *key* is a single :class:`int`, :class:`float`, :class:`unicode`
        value, it returns a list containing only this value. If the *key* is a
        list, this list is returned. If the key does not exists, an empty list
        is returned. Else, a :exc:`TypeError` is raised.
        """
        try:
            value = self[key]
        except KeyError:
            if default_value is not _sentinel:
                return default_value
            return []

        if value is None and default_value is not _sentinel:
            return default_value
        if isinstance(value, list):
            return value
        if (isinstance(value, (basestring, int, float, long)) and
            not value is True and not value is False):
            return [value]
        raise TypeError('{key} is not a list nor an int or a string but a {actual}'.format(
            key=key, actual=type(value).__name__))

    @staticmethod
    def get_default(value=None):
        """
        Get a value on the default conf instance.

        The default conf instance is set by :meth:`get_default`.
        """
        if BaseConf._default is None:
            raise ValueError('Configuration is not loaded')
        if value is None:
            return BaseConf._default
        else:
            return BaseConf._default.get(value)

    @staticmethod
    def set_default(instance):
        """
        Set the default Conf instance.

        :meth:`set_default` must be called before :meth:`get_default`.
        """
        if instance is None:
            BaseConf._default = None
            return None

        if not isinstance(instance, BaseConf):
            raise TypeError('value must be an instance of the class')
        BaseConf._default = instance
        return instance


class Conf(BaseConf):
    """
    A simple Conf.

    It takes a dict of values and returns it with the augmented methods
    of :class:`BaseConf`.
    """
    def __init__(self, values):
        self._values = values

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __getitem__(self, key):
        return self._values[key]


class EmptyConf(BaseConf):
    """
    Empty Configuration Object
    """

    def __iter__(self):
        return iter([])

    def __len__(self):
        return 0

    def __getitem__(self, value):
        raise KeyError('This conf object is empty')

    def __nonzero__(self):
        return False

    def __contains__(self, key):
        return False
