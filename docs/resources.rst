==============================
Resources, collections and ids
==============================

Napix uses the REST structure to help you leverage your assets and monetize through efficient analytics and data-mining.

The REST method uses HTTP to invoke procedures on specified resources.
The resources are designated by an URI.
They are hierarchically sorted and separated by slashes.
Every character are allowed in the URI, although they may need to be escaped
For example, if a ``file`` manager takes file path as IDs. ``/file/%2Fusr%2fbin%2fgcc`` refers to the resource '/usr/bin/gcc'

IDs
===

Within Napix, every token between two ``/`` that does not start with _napix_ is an ID.

Every thing that starts with _napix_ is reserved.

Collections
===========

The collections are a set of resources.
The collections have an URI ending with a ``/``.

In Napix the managers subclasses of :class:`~managers.Manager` instances represent collections.
They are instantiated with the parent that spawned them.

Resources
=========

Resources are objects managed in Napix.
They behave like dictionaries.
