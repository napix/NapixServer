.. _storage:

=============
Local stotage
=============

Napix proposes an mechanism for easy storage of dict-like objects,
and integers.

Usage
=====

.. currentmodule:: napixd.store

Mappings
--------

The :class:`Store` is factory function to generate a
:class:`backends.BaseStore`.

The :class:`backends.BaseStore` and :class:`backends.Store` are
:class:`collections.MutableMapping` sub-classes, the first is a synchronous implementation
and the other an asynchronous implementation.

Synchronous implementations propagates modifications from and to the persistence layer immediately.
Asynchronous implementations write the modifications in the persistence layer after
:meth:`Store.save` is called.

Calling :class:`BaseStore.save` does nothing.

.. code-block:: python

   def create_resource(self, resource_dict):
        id = self.generate_new_id()

        store = Store(self.get_name())
        store[id] = resource_dict
        store.save()

        return id


Counters
--------

Counters allow to make atomic operations on an integer.
They implement :meth:`Counter.increment` and :meth:`Counter.decrement`.

.. code-block:: python

   def generate_new_id(self, resource_dict):
        """Generate a new ID from a sequence"""
        return Counter(self.get_name()).increment()

They can be used as a context manager.
The value is increment at the enter and decremented at the exit.

Built-in backends
=================

.. currentmodule:: napixd.store.backends

The built-in backends implements common storing and sharing strategies.

Synchronous shared Storage
--------------------------

* :class:`redis.RedisHashStore`
* :class:`redis.RedisKeyStore`

Asynchronous shared Storage
---------------------------

* :class:`redis.RedisStore`

Asynchronous local Storage
--------------------------

* :class:`file.FileStore`
* :class:`file.DirectoryStore`
