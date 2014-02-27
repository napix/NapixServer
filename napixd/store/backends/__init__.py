#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections

"""
=====================
Store implementations
=====================

Here are the base classes for the implementations of the backends
used by :mod:`napixd.store`

Mechanism
=========

The implementation of store and counter backends uses two classes (or callable):
the Backend and the Store (or the counter)

The backend
-----------

The backend is an object that prepares the Stores.
The backend is called with the collection and returns a Store instance.

Its initialized with the parameters either
from the configuration or from the user.
A Backend is reusable and may generate multiple Stores.

The :class:`BaseBackend` class may be used
as a starting point but it's not required.
In simple cases, the backend may just be a function that returns a Store class

The Store
---------

The :class:`Store instance<napixd.store.Store>`
is the object handled to the user.
It is built by the Backend.

Implementations strategies
==========================

Asynchronous implementations
----------------------------

Asynchronous implementations requires the user to call
:meth:`~BaseStore.save` on the store after a modification has been made.

:class:`Store` is the base class of asynchronous implementations and require
to override the ``save`` method.

Synchronous implementations
---------------------------

Synchronous implementations directly commit the modifications
to the underlying persistance support.
Setting a value from a place and getting it after returns the same data,
whatever the order of the creation of the stores.

:class:`Counters<napixd.store.Counter>` are synchronous implementations.

:class:`BaseStore` is the base class of synchronous implementations and require
to override ``keys``, ``__getitem__``, ``__setitem__`` and `__delitem__``.

"""


class BaseBackend(object):

    """
    The base backend.

    ``config`` come either from the config file or
    is manually specified by the user.
    """

    def __init__(self, config):
        pass

    def __call__(self, collection):
        """
        Builds the Store instance with the class from :meth:`get_class`
        and the arguments from :meth:`get_args`.
        """
        cls = self.get_class()
        args, kw = self.get_args(collection)
        return cls(*args, **kw)

    def get_class(self):
        """
        Returns the Store class
        """
        return BaseStore

    def get_args(self, collection):
        """
        Returns the arguments required by the Store class
        """
        return (collection,), {}

    def keys(self):
        """
        List all the collections created by this backend.
        """
        raise NotImplementedError

    def dump(self):
        """
        Dump all the collections and their content in a mapping of dicts.
        """
        return dict((collection, dict(self(collection).items()))
                    for collection in self.keys())

    def load(self, collections):
        """
        Load the keys from a mapping of collections
        """
        for name, content in collections.items():
            collection = self(name)
            collection.update(content)
            collection.save()

    def drop(self):
        """
        Remove all the keys of this backend
        """
        for key in self.keys():
            self(key).drop()


class BaseStore(collections.MutableMapping):

    def __init__(self, collection):
        self.collection = collection

    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__, self.collection)

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def save(self):
        pass

    def drop(self):
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.exception_type is None:
            self.save()


class Store(BaseStore):

    def __init__(self, collection, data):
        super(Store, self).__init__(collection)
        self.data = data or {}

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def keys(self):
        return self.data.keys()

    def incr(self, key, incr=1):
        self[key] += 1
        return self[key]

    def drop(self):
        self.data = {}

    def save(self):
        raise NotImplementedError


class BaseCounter(object):
    """
    Base class for counters.

    Counters implement the context manager protocol.
    Entering the context, increase :attr:`value` by one and
    returns the new value.
    Exiting with or without exception decreases by one.

    >>> c = Counter('name')
    >>> c.increment()
    >>> print c.value
    1
    >>> with c as v:
    ...     print v
    2
    >>> print c.value
    1

    .. attribute:: value

        The current value of the counter
    """
    def __enter__(self):
        return self.increment(1)

    def __exit__(self, exception_type, exception_value, traceback):
        self.decrement(1)

    def decrement(self, by=1):
        return self.increment(-by)

    def increment(self, by=1):
        raise NotImplementedError()

    def reset(self, to=0):
        raise NotImplementedError()

    def __repr__(self):
        return '{0} ={1}'.format(self.__class__.__name__, self.value)
