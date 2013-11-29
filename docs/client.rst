.. currentmodule:: napixd

.. _client:

===============================
Doing requests on other servers
===============================

The :mod:`client` proposes facilities to run requests on other Napix servers.

The request requires a :class:`napix.connection.Connection` to an host and
an :mod:`authentication provider<napix.authenticators>`.

The helper class :class:`client.Client` is provided to manages this connection.
The class takes a destination host and an authenticator.
Its method :meth:`client.Client.request` send requests to the destination.

>>> from napixd.client import Client
>>> from napix.authenticators import TokenIdentifier
>>> c = Client('server.napix.nx',
...         authenticator=TokenIdentifier('de72457df438272d8d05a0823289084811813c07'))
>>> resp = c.request('GET', '/')
>>> resp.body
['/abc', '/captain']

Common scenarios with the classic authentication method by *login* and *key*,
are handled directly.

>>> from napixd.client import Client
>>> c = Client('server.napix.nx', {'login': 'root', 'key': 'toor'})
>>> c.request('GET', '/')

Errors
======

When an error occurs during a request, a :exc:`napix.exceptions.HTTPError` is raised.
If it's not caught, the error is caught by the
:class:`~napixd.plugins.exceptions.ExceptionsCatcher` and the details are transfered
to the user making the query.

The details are: the original network call in ``remote_call`` and the
error response in the ``remote_error``.
The error response may be a string of the error like ``"404 NOT FOUND" `10` not found``
or a full exception detail like returned by the :class:`~napixd.plugins.exceptions.ExceptionsCatcher`
of the remote server.

An exception can bubble through multiple Napix servers.


Doing mutliple request simultaneously
=====================================

.. currentmodule:: napixd.client

The :class:`pool.ClientPool` class instanciates and manages multiples
:class:`gevent.Client` doing request simultaneously on different servers
or on the same server.

The :class:`pool.ClientPool` automatically creates :class:`gevent.Client` for each host.
If an more than one request are needed on a single server,
only one :class:`~gevent.Client` instance is created.

The *simultaneous* parameter of :class:`pool.ClientPool` is the maximum number
of concurrent connections on the destination.
The default value is 2.

>>> c = ClientPool(TokenIdentifier('de72457df438272d8d05a0823289084811813c07'))
>>> c.request('server.napix.nx', 'GET', '/')
>>> c.wait()
['<Response 200 OK>']

In order to get the responses, the methods :meth:`~pool.ClientPool.wait` or
:meth:`~pool.ClientPool.wait_unordered` returns the responses of the requests.
Responses are either the :class:`napix.connection.Response` returned
or the :class:`napix.exceptions.HTTPError` raised.

The :meth:`~pool.ClientPool.wait` method returns the responses once they all completed,
by returning or raising in the same order as they have been added.

.. code-block:: python

    def create_resource(self, resource_dict):
        cp = ClientPool(authenticator)
        cp.request('ip-allocator.enix.org', 'POST', '/vm-ip/', {
            'size': 1
        })
        cp.request('filer.enix.org', 'POST', '/storage/', {
            'size': 10**9,
        })
        # wait until the filer and ip are ready
        ip, filer = cp.wait()

        if ip.status != 204:
            raise ValueError('Cannot get IP')
        elif filer.status != 204:
            raise ValueError('Cannot get storage')

        # ...

The method :meth:`~pool.ClientPool.wait_unordered`, returns the responses as they complete.

.. code-block:: python

    def create_resource(self, resource_dict):
        cp = ClientPool(authenticator)
        for x in self.xen_servers:
            cp.request(x, 'GET', '/capacity/capacity')

        server = None
        for response in cp.wait_unordered(timeout=10):
            # wait up to 10 seconds for the server
            if response.status != 200:
                # disregard failures
                continue
            if response.body['size'] < EXPECTED:
                # disregard non suitable responses
                continue

            # take the first one.
            server = response.request.host
            break
        else:
            raise ValueError('No server available')

        # ...
