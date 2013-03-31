#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
==================
Persistent objects
==================

Napix provides a facility to make simple persistent objects.

In this module, lie the objects used by the end users.
See more details on the implementation strategies in :mod:`napixd.store.backends`.

Store
=====

.. data:: DEFAULT_STORE

    The default Store class. This parameter is overriden by the configuration value :ref:`Napix.storage.store<conf.napix.storage>`.

    The default is :class:`napixd.store.backend.file.FileBackend`.

.. class:: Store( collection, backend='default', **options)

    Stored objects behaves like dict and store content for a given ``collection``.

    ``collection`` is the name of the object to store or retrieve.

    They support, getting, setting, deleting keys, :meth:`keys`, :meth:`values`, etc.

    They also have a :meth:`drop` method that remove the persisted collection from the storage.

    Stored objets can be either synchronous or asynchrounous, meaning that an operation is
    directly done to the storage or have to wait a :meth:`save`

    Each StoreBackend implementation may choose its own optional arguments.
    For example, a Store based on the filesystem may choose to get a base directory as an option.

    .. method:: save

        Persists the content of the store.

        Does nothing if the backend is synchronous.

    .. method:: drop

        Cleans the content of the stored object and removes the collection from the storage.

Counters
========

.. data:: DEFAULT_COUNTER

    The default Counter class. This parameter is overriden by the configuration value :ref:`Napix.storage.counter<conf.napix.storage>`.

    The default is :class:`napixd.store.backend.local.LocalCounterBackend`.

.. class:: Counter( name, backend='default', **options)

    Counters are simple class that make atomic operations on an integer.

    .. code-block:: python

        id_generator = Counter('my-service-id')
        def generate_new_id(self, resource_dict):
            return 'scp-%03i' % self.id_generator.increment()

    .. attribute:: value

        The current value of the held integer.

    .. method:: increment( by = 1) -> int

        Atomically augment the value by the ``by`` parameter, and returns its value.


    .. method:: reset( to = 0) -> int

        Atomically reset the value to the ``to`` parameter and returns the old value.

"""

import sys
from napixd.conf import Conf

__all__ = ( 'NoSuchStoreBackend', 'Store', 'Counter')

DEFAULT_STORE = 'napixd.store.backend.file.FileBackend'
DEFAULT_COUNTER = 'napixd.store.backend.local.LocalCounter'

class NoSuchStoreBackend(Exception):
    """Exception raised when a backend can not be imported."""
    pass

def Store(collection, backend='default', **opts):
    """
    Returns a store constructed with the given ``backend``.

    The keyword arguments ``options`` depends on the backend.

    The backend is a string coding the dotted python path to a backend class or
    only the class name if the backend is one of standard backends in :mod:`napixd.store.backends`.

    It raises a :exc:`NoSuchStoreBackend` if the string does not resolve to a class.

    .. code-block:: python

        from napixd.store import Store

        default_store = Store('collection_name')
        this_store = Store('collection_name', backend='RedisHashKey', host='redis.example.com')
        that_store = Store('collection_name', backend='company.dbframework.NapixStoreBackend')

        default_store.keys()
        [ 'value', 'value1', 'value2' ]

        this_store['value']
        12

        that_store['value'] = 123
        that_store.save()

    """
    backend = loader.get_backend(backend, opts, DEFAULT_STORE)
    return backend( collection)

def Counter( name, backend='default', **opts):
    """
    Returns a counter with the specified ``backend`` and the given ``name``.
    See :func:`Store` for more details.
    """
    backend = loader.get_backend(backend, opts, DEFAULT_COUNTER)
    return backend( name)

class Loader(object):
    """
    Loader for the store and counter backends
    """
    def __init__(self):
        self.conf = Conf.get_default('Napix.storage')
        self._class_cache = {}
        self._backend_cache = {}

    def _get_class(self, fqdn):
        if not fqdn in self._class_cache:
            module, dot, classname = fqdn.rpartition('.')
            if not module:
                raise NoSuchStoreBackend('Cannot import %s, Only full dotted names can be used'%fqdn)
            try:
                __import__(module)
                self._class_cache[fqdn] = getattr( sys.modules[module], classname)
            except (ImportError, AttributeError):
                raise NoSuchStoreBackend, fqdn
        return self._class_cache[fqdn]

    def _get_backend(self, backend, opts):
        cls = self._get_class( backend)
        return cls( opts)

    def _get_backend_conf(self, backend):
        if backend not in self._backend_cache:
            self._backend_cache[backend] = self._get_backend( backend, self.conf.get( backend))
        return self._backend_cache[backend]

    def get_backend(self, backend, opts, default):
        """
        Get the backend name ``backend``.
        If opts are specified, the backend is instanciated with those options.
        Else the backend is created and cached with the options from the config.
        """
        if backend == 'default' or backend is None:
            backend = default

        if opts:
            return self._get_backend( backend, opts)
        else:
            return self._get_backend_conf( backend)

loader = Loader()
