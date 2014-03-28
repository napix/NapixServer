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

    def get_resource(self, url):
        path = url.split('/')
        if path[0] != '':
            raise ValueError('get_resource is called with a path starting by a "/"')
        if path[-1] == '':
            raise ValueError('get_resource is called with a path not ending with a "/"')

        managers = path[1::2]
        ids = path[2::2]
        service = self.napixd.get_service(path[1])

        cs = service.get_collection_service(managers)
        resource = FetchResource(
            CollectionContext(cs, self.napixd,
                              method='GET'), ids)
        return resource.handle()


class FetchResource(ServiceResourceRequest):
    def get_callback(self):
        return None

    def call(self):
        return self.resource
