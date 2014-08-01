#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sources of authentication from the request.

Each source is a :func:`callable`.
The source is called with the request and returns ``None`` if it cannot extract informations
or a dict with the values it has got.
The first source returning a non ``None`` value is used for the providers.
"""


import urlparse

from napixd.http.response import HTTPError


class CatchAllSource(object):
    def __call__(self, request):
        return {
            'is_secure': False
        }


class SecureAuthProtocol(object):
    """
    Implements the secure-auth provider.

    The *Authorization* header of the requests is checked.
    """
    def __init__(self):
        self._mandatory = frozenset(['path', 'host', 'method'])

    def __call__(self, request):
        if 'Authorization' not in request.headers:
            return None

        msg, l, signature = request.headers['Authorization'].rpartition(':')
        if l != ':':
            return None

        content = urlparse.parse_qs(msg)
        for x in content:
            content[x] = content[x][0]

        missing_keys = self._mandatory.difference(content)
        if missing_keys:
            raise HTTPError(403, 'Missing authentication data: {0}'.format(
                ', '.join(missing_keys)))

        content.update({
            'msg': msg,
            'signature': signature,
        })
        return content


class NonSecureAuthProtocol(object):
    """
    Implements the Non-secure authentication protocol.

    A token in the GET parameters is checked.
    """
    @classmethod
    def from_settings(cls, settings):
        token = settings.get('get_parameter', 'token')
        return cls(token)

    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        if self.token not in request.GET:
            return None
        login, l, signature = request.GET[self.token].partition(':')
        if l != ':':
            raise HTTPError(401, 'Incorrect NAPIX non-secure Authentication')
        return {
            'login': login,
            'signature': signature,
            'msg': login,
            'is_secure': False
        }
