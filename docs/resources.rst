==============================
Resources, collections and ids
==============================

Napix uses a few concepts with the REST structure.
Objects are linked to an URI.
There are two sort of objects, the collections and the resources.

Resources and collections are separated by ``/``.
An id containing ``/`` must escape them.
If a ``file`` manager takes file path as IDs,
``/file/%2Fusr%2fbin%2fgcc`` refers to the resource '/usr/bin/gcc'

The escaping and unescaping is handled by the Napix server in input and output.

.. note::

    The identifier cannot start with **_napix_**

    Those identifiers are reserved.

Collections
===========

The URI of the resources ends by by a ``/``.

The collections are a set of resources.
A collection is managed by a :class:`~napixd.managers.base.Manager`, and defines how to list its resources, create a new one,
fetch, modify and remove each resource.

A Manager is a *root* manager if it is the first manager after the slash.
All the managers after the first are *sub-managers*.
They hold a :attr:`~napixd.managers.base.Manager.parent` property
that link to the resource that spawned them.

For instance: ``/host/127.0.0.1/ports/``, ``/ports/`` sub-manager has been instantiated
with the resource ``/host/127.0.0.1``.


Resources
=========

Resources are objects managed in Napix.
They contains a set of properties.
The properties are defined from the :class:`~napixd.managers.base.Manager.resource_fields` of the class.

The resource fields declaration tells to the Napix server how to extract,
document, validate, etc the fields from and to the JSON representation.

The resource fields are also used by the introspection to advise the consumers of the usage of each field.

See :mod:`napixd.managers.resource_fields` for the fields required and the options of the resource_fields.
