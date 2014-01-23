#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json
import collections
from urllib import unquote

from cStringIO import StringIO
from napixd.http.response import HTTPError
from napixd.http.headers import HeadersDict

__all__ = ['Request']


class lazy(object):
    def __init__(self, fn):
        self.fn = fn

    def __get__(self, instance, owner):
        if instance is None:
            return self.fn
        instance.__dict__[self.fn.__name__] = value = self.fn(instance)
        return value


class Query(collections.Mapping):
    def __init__(self, raw):
        if isinstance(raw, basestring):
            values = collections.defaultdict(list)
            for bit in raw.split('&'):
                if '=' in bit:
                    key, value = bit.split('=', 1)
                    values[unquote(key)].append(unquote(value))
                else:
                    values[unquote(bit)].append(None)
        elif isinstance(raw, Query):
            values = dict()
            for key in raw:
                values[key] = raw.getall(key)
        elif isinstance(raw, collections.Mapping):
            values = dict()
            for key, value in raw.items():
                values[key] = [value]
        elif isinstance(raw, collections.Iterable):
            values = collections.defaultdict(list)
            for key, value in raw:
                values[key].append(value)
        else:
            raise TypeError('value is instanciated with a dict or a string')

        self.values = dict(values)

    def getall(self, key):
        if not key in self.values:
            return []
        return self.values[key]

    def __contains__(self, key):
        return key in self.values

    def __getitem__(self, key):
        if not key in self.values:
            raise KeyError(key)

        return self.values[key][0]

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)


class InputStream(object):
    def __init__(self, stream, clen):
        self._length = clen
        self._stream = stream

    def read(self, size=-1):
        if self._length == 0:
            return ''

        if size == -1:
            size, self._length = self._length, 0
        else:
            size = min(size, self._length)
            self._length -= size

        return self._stream.read(size)


class Request(object):
    """
    A request object.

    *environ* is the WSGI mapping.
    """
    MAX_REQ_SIZE = 10 * 1e6  # 10M

    def __init__(self, environ):
        self.environ = environ
        self.method = environ['REQUEST_METHOD']
        self.path = environ['PATH_INFO'] or '/'

    def __repr__(self):
        return 'Request: {method} {path}'.format(**self.__dict__)

    @lazy
    def content_type(self):
        """The content-type of the request"""
        return self.environ.get('CONTENT_TYPE') or 'application/octet-stream'

    @lazy
    def content_length(self):
        """The content-length of the request parsed as an int"""
        try:
            value = int(self.environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            return 0

        if value >= 0:
            return value
        return 0

    @property
    def query_string(self):
        """The string of the values after the ?"""
        return self.environ.get('QUERY_STRING') or ''

    @lazy
    def query(self):
        """
        The parsed version of the :attr:`query_string`.
        """
        return Query(self.query_string)

    @property
    def GET(self):
        """The same as :attr:`query`"""
        return self.query

    @lazy
    def headers(self):
        """The :class:`~napixd.http.headers.HeadersDict` of the HTTP headers"""
        return HeadersDict((key[5:], value)
                           for key, value in self.environ.items()
                           if key.startswith('HTTP_'))

    def _body(self):
        if self.content_length == 0:
            return StringIO('')
        if self.content_length > self.MAX_REQ_SIZE:
            raise HTTPError(413, 'Request too large')

        return InputStream(self.environ['wsgi.input'], self.content_length)

    @lazy
    def data(self):
        """
        The parsed version of the request if it is a JSON request.

        Raises a 415 Unsupported Media Type for other content-types
        """
        if not self.content_type or not self.content_length:
            return {}
        elif self.content_type.startswith('application/json'):
            if not isinstance(self.json, dict):
                raise HTTPError(400, 'json object is not a dict')
            return self.json

        raise HTTPError(415, 'This method only accepts application/json')

    @lazy
    def json(self):
        try:
            return json.load(self._body())
        except ValueError:
            raise HTTPError(400, 'Misformated JSON object')
