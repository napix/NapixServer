
"""
=======================================
Authentication infrastructure of Napix.
=======================================

The authentication in napixd is handled by the :class:`plugin.AAAPlugin`.

This plugin takes a list of :ref:`auth.sources` and another list of :ref:`auth.providers`

.. _auth.sources:

Sources
=======

Sources are callable objects. They are called with the
:class:`napixd.http.request.Request` object.

The role of the sources is to get from the requests all the elements
used for the authentication. The request may contains the informations in
various places like the :class:`GET paramaters<sources.NonSecureAuthProtocol>`
or the :class:`Authorization header<jwt.JSONWebToken>` and various encodings.

There are 3 outcomes from the call of an source.

* The source has not information to extract and returns ``None``.
  Eg: the source expects an header that is not present.
  The next source in the list is called.
* The source can extract informations and returns them as a dict.
  The next source in the list is not called and the plugin proceed to call
  the :ref:`auth.providers`.
* The source is sure it is the target of the encoded informations but it
  cannot decode them, for instance because of misformatted text. It raises a
  :exc:`napixd.http.response.HTTPError`. The plugins does not catch it and
  it halts the authentication process.

When all the sources returns ``None``, a HTTP *401 Unauthorized* response
is returned and the authentication is stopped.

.. _auth.providers:

Providers
=========

Providers are callable objects. They are called with the request and the value
returned by the :ref:`source<auth.sources>`.

Providers should, when they are applicable checks that the request is authorized.

There are 3 outcomes from the call of an provider.

* The provider can not authoritatively decide if the request is sufficiently
  authenticated and returns ``None``. Eg: The :class:`request.HostChecker`
  checks that the requets and the signed values match. If they match, it cannot
  alone tell if the request is authorized.
  The next provider is called by the plugin.
* The provider is sure that the request is authorized and returns a truthy
  object like ``True`` or a ``function``. The plugin finishes the authentication
  process and executes the callback. If the truthy object is callable, it will
  be used as a filter for the response.
* The provider is sure that the request is not authorized and returns ``False``.
  The plugin stops the authentication process and raises a *403 Forbidden* HTTP
  response.

If there is not source that returns ``True``, a *403 Forbidden* response is sent
and the authentication process stopped.

"""
