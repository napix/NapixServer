==============
Authentication
==============

The napixd use a central authentication server that authentifies the user,
checks if the user has the permissions and logs it.

.. _protocol:

Protocol
========

Request authentication data:

+-----------+--------+----------------------------+-------------------+
| Parameter | Type   | Definition                 | Example           |
+===========+========+============================+===================+
| timestamp | float  | Timestamp of the request   | 1345195098.769764 |
+-----------+--------+----------------------------+-------------------+
| Login     | string | Name of the alias the user |  user             |
|           |        | is using to sign its       |                   |
|           |        | request                    |                   |
+-----------+--------+----------------------------+-------------------+
| method    | string | Method of the request      | GET               |
+-----------+--------+----------------------------+-------------------+
| host      | string | Target host of the request | napix.example.com |
+-----------+--------+----------------------------+-------------------+
| path      | string | Request path               | /collection/      |
+-----------+--------+----------------------------+-------------------+
| nonce     | string | Random string. Used to     | ezmdsb34sers3gopf |
|           |        | avoid replay of request    |                   |
+-----------+--------+----------------------------+-------------------+

All those parameters are URI encoded and then signed with the key of the alias used.

Client
------

Before the request starts, an identifier and a secret key are shared between the 
authentication server of the realm and the client.

For each request, the client generate a random unique string,
get the timestamp, add the detail of the request (method, host, path).
Thoses data are urlencoded and the resulting string is signed with the client's secret key.

Then it sends the result and the signature joined  by a ':' in the `Authorization` HTTP header.

Server
------

The server receive the request, it unserializes the request data and checks 
that the data that were signed are the actual request.
It checks that the destination is itself, by checking that the ``host`` parameter
of the request corresponds to the ``Napix.auth.service`` configuration key.

Then it sends the request to the central server at the url pointed by ``Napix.auth.auth_url``
and if it returns a 200, it runs the request.

Central
-------

The central server retrieves the user that signed the request,
and checks the signature against the key.

If eveything is in order, it returns 200 OK,
else it return a 400 if the request has not been understood or
403 if the request was correct but the authorization has not been granted.


Napixd pluggable authentication
===============================

The authentication layer is provided by a plugin :class:`plugins.AAAPlugin`.
This plugin is not automatically installed by :class:`loader.NapixBottle`.

This plugin is loaded if a key ``Napix.auth`` exists in the configuration file.


Custom central server
---------------------

The central server receives a POST with the parameters given in :ref:`protocol`,
and additional keys `msg` which is the original message and `signature` which
is the signature of `msg` by the user.

If the central server accepts the request, it returns a 200 OK response,
and the napixd server executes the request.
If it denies the request, it returns a 403 FORBIDDEN response,
and the napixd returns also a 403.

Every other response possible will cause the request to be denied and will be reported as an error
by the napixd server and will return to the user as a 500 INTERNAL ERROR.

