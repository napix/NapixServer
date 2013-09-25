.. currentmodule:: napixd

.. _client:

===============================
Doing requests on other servers
===============================

The :mod:`client` proposes facilities to run requests on other Napix servers.

The request requires a :class:`napix.connection.Connection` to an host and
an :mod:`authentication provider<napix.authenticators>`.

The :class:`helper class Client<client.Client>` provides a constructor
for common scenarios with the classic authentication method by *login* and *key*.

>>> from napixd.client import Client
>>> c = Client('server.napix.nx', {'login': 'root', 'key': 'toor'})
>>> c.request('GET', '/')

Using the client
================

The raw client :class:`napix.connection.Connection` may be used directly.
The exception mechanism will still work.

>>> from napix.connection import Connection
>>> from napix.authenticators import TokenIdentifier
>>> c = Client('server.napix.nx', TokenIdentifier('de72457df438272d8d05a0823289084811813c07'))
>>> resp = c.request('GET', '/')
>>> resp.body
['/abc', '/captain']

Errors
======

When an error occurs during a request, a :exc:`napix.exceptions.HTTPError` is raised.
If it's not caught, the error is caught by the
:class:`~napixd.plugins.exceptions.ExceptionsCatcher` and the details are transfered
to the user making the query.

The details are: the original network call in ``remote_call`` and the
error response in the ``remote_error``.
The error response may be a string of the error like ``"404 NOT FOUND" `10` not found``
or a full exception detail like returned by the ::class:`~napixd.plugins.exceptions.ExceptionsCatcher`
of the remote server.

An exception can bubble through multiple Napix servers.
