#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Client lib of napix.

It uses the :mod:`napix` to do requests.


.. class:: Client

    IF gevent is available, :class:`gevent.Client`
    else :class:`client.Client`.

.. exception:: HTTPError

    Convenience import of :exc:`napix.exceptions.HTTPError`
"""

from napix.exceptions import HTTPError

try:
    from napixd.client.gevent import Client
except ImportError:
    from napixd.client.client import Client

__all__ = ('Client', 'HTTPError')
