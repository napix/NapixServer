
.. module:: store.backends

=====================
Store implementations
=====================

Implementations of :class:`StoreBackend`.

Asynchronous implementations
============================

Synchronous implementations needs the user to call :meth:`.save<StoreBackend.save>`
on the store after a modification has been made.

.. class:: FileStore(path)

    Store based on files.
    The collection is a file containing pickled datas.

    It takes an optional `path` argument that indicates the directory which contains
    the collections.
    If it is not given, the configuration key ``Napix.storage.file.path`` is used.

.. class:: RedisStore(host,port)

    Store based on a key in a Redis server.

    It takes optional `host` and `port` arguments to indicate to which server it connects to.
    If they are not given, the configuration key ``Napix.storage.redis.{host,port}`` are used.


Synchronous implementations
===========================

Asynchronous implementations directly commit the modifications to the underlying persistance support.
Setting a value from a place and getting it after returns the same data,
whatever the order of the creation of the stores.

.. class:: RedisHashStore(host,port)

    Store based on Redis Hashes.
    Every value of the store is a value of a Redis hash.

    cf :class:`RedisStore` for the keyword arguments and connection options.

.. class:: RedisKeyStore(host,port)

    Store based on Redis keys
    Every value of the store is a value of a Redis key.

    cf :class:`RedisStore` for the keyword arguments and connection options.
