
.. module:: store

==================
Persistent objects
==================

Napix provides a facility to make simple persistent objects.


.. exception:: NoSuchStoreBackend

    When a backend can not be imported.

Store
=====

.. class:: StoreBackend( collection, options)

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

.. function:: Store( collection, backend=None, options)

    Returns a store constructed with the given ``backend``.

    The keyword arguments ``options`` depends on the backend.

    The backend is a string coding the dotted python path to a backend class or
    only the class name if the backend is one of standard backends in :mod:`store.backends`.

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



Counters
========

.. class:: CounterBackend( name, options)

    Counters are simple class that make atomic operations on an integer.

    .. code-block:: python

        id_generator = Counter('my-service-id')
        def generate_new_id(self, resource_dict):
            return 'scp-%03i' % self.id_gen.increment()

    .. attribute:: value

        The current value of the held integer.

    .. method:: increment( by = 1) -> int

        Atomically augment the value by the ``by`` parameter, and returns its value.


    .. method:: reset( to = 0) -> int

        Atomically reset the value to the ``to`` parameter and returns the old value.

.. function:: Counter( name, backend=None, options)

    Returns a counter with the specified ``backend`` and the given ``name``.
    See :func:`Store` for more details.

