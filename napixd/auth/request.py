#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Request data checker.

Those classes checks that the request data are conform
and that request signed is the request actually being done.
"""

from napixd.http.response import HTTPError


class GlobalPermissions(object):
    """
    Authorizes the request granted by *permset* for anynone
    """
    def __init__(self, permset):
        self._permset = permset

    def __call__(self, request, content):
        host = request.headers['host']
        method = request.method
        path = request.path

        if self._permset.authorized(host, method, path):
            return True
        return None


class HostChecker(object):
    """
    Checks that the target host is one of the authorized hosts.
    """
    def __init__(self, hosts):
        self.hosts = frozenset(hosts)

    def __call__(self, request, content):
        host = content.get('host')
        if host is None:
            return None
        if request.headers['host'] != host:
            raise HTTPError(403, 'Bad authentication data host does not match')
        if host not in self.hosts:
            raise HTTPError(403, 'Bad host')
        return None


class RequestParamaterChecker(object):
    """
    Check that the method and the path are the same as the extracted data.
    """
    def __call__(self, request, content):
        actual_path = request.path
        if request.query_string:
            actual_path += '?' + request.query_string

        signed_method = content.get('method')
        if signed_method is not None and signed_method != request.method:
            raise HTTPError(403, 'Bad authorization data method does not match')

        signed_path = content.get('path')
        if signed_path is not None and signed_path != actual_path:
            raise HTTPError(403, 'Bad authorization data path does not match')

        return None
