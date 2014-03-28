#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.services.requests.resource import (
    ServiceResourceRequest
)


class NapixdContext(object):
    def __init__(self, napixd, request):
        self.request = request
        self.napixd = napixd
        self.method = request.method
        self.parameters = request.GET
        self.data = request.data

    def get_service(self, service):
        return self.napixd.find_service(service)


class CollectionContext(object):
    def __init__(self, cs, napixd_context, method=None):
        self.napixd = napixd_context
        self.service = cs
        if method is not None:
            self.method = method

    def __getattr__(self, attr):
        return getattr(self.napixd, attr)

    def get_manager_instance(self, path):
        return self.service.get_manager(path, self)
