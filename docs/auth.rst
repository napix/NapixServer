========================
Authentication protocols
========================


Napix implements an authentication protocol.
This protocol uses cryptographic technics to garantee the authenticity of the user.

There is a default protocol, and exceptions to this protocol
that can be enabled by :ref:`options`.


The Standard Protocol
=====================

By default, the protocol requires that the users signs his request with an HMAC signature
unique to each request.

When a Napix Server recieve a request, its checks that the values signed by the user
correspond to the actual request parameters, then it submits the request to its Napix Server.

The host
--------

The Napix server can limit the DNS domains that redirect to the server.

The conf value :ref:`Napix.auth.host<conf.napix.auth>` can be a string or
a list of strings of allowed domains names.
If the list is defined, only requests where the host header is one of the defined values
will be executed, other will result in a 403 error.


Napix Central
=============

A Napix server delegates the check of authentication and authorisation
to a third-party host running a Napix Central server.

The endpoint of the authentication is defined by the :ref:`Napix.auth.auth_url<conf.napix.auth>`.
The Napix Server must be able to reach the Central server,
but the client has not to communicate with the Central.

.. _non-secure-auth:

Non secure authentication
=========================

Napix implements a less secured, but more practical authentication protocol.
This protocol requires only a GET paramater ``token``.

This protocol is called non-secure, because if a request is seen by a sniffer or an attacker
he can pass as the original user.

.. note::

   ``token`` is the default GET paremeter.
   Its name can be changed by setting :ref:`Napix.auth.get_parameter<conf.napix.auth>` in the conf.


.. _autonomous-auth:

Autonomous authentication protocol
==================================

Napix have an autonomous protocol.
This protocol is implemented with the same interface as the standard secure protocol.
But for the local login, the source of authentication is not the central but a password set in local.

The credentials are set in the conf by the values :ref:`Napix.auth.login et Napix.auth.password<conf.napix.auth>`.
Trying to enable the autonomous authentication without having set a password will prevent the server from running.

