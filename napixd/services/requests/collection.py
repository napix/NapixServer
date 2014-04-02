#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections

from napixd.services.methods import Implementation
from napixd.services.requests.http import HTTPMixin, MethodMixin
from napixd.services.requests.base import ServiceRequest
from napixd.http.response import HTTPResponse


class ServiceCollectionRequest(ServiceRequest):
    """
    ServiceCollectionRequest is an implementation of :class:`ServiceRequest`
    specialized for Collection requests (urls ending with /)
    """

    def get_manager(self):
        """
        Returns an :class:`napixd.services.methods.Implementation`
        of the manager.
        """
        manager = super(ServiceCollectionRequest, self).get_manager()
        return Implementation(manager)

    def check_datas(self):
        """
        Checks the data when the :class:`ServiceCollectionRequest` intends
        to call :meth:`napixd.managers.Manager.create_resource`.
        """
        if self.method != 'POST':
            return super(ServiceCollectionRequest, self).check_datas()

        data = self.context.data
        return self.manager.validate(data, None)


class HTTPServiceCollectionRequest(MethodMixin, HTTPMixin, ServiceCollectionRequest):
    METHOD_MAP = {
        'filter': 'list_resource_filter',
        'getall': 'get_all_resources',
        'getall+filter': 'get_all_resources_filter',
        'POST': 'create_resource',
        'GET': 'list_resource',
        'HEAD': 'list_resource'
    }

    def serialize(self, result):
        if self.method == 'HEAD':
            return None
        elif self.method == 'POST':
            if result is None:
                raise ValueError('create_resource method must return the id.')
            url = self.make_url(result)
            return HTTPResponse(201, {'Location': url}, None)
        elif self.method.startswith('getall'):
            if not isinstance(result, collections.Iterable):
                raise ValueError('get_all_resources returned a non-iterable object')

            pairs = list(result)
            if not all(len(pair) == 2 for pair in pairs):
                raise ValueError('get_all_resources must return a iterable of tuples')

            return dict(
                (self.make_url(id), self.manager.serialize(resource))
                for id, resource in result)
        elif self.method == 'GET' or self.method == 'filter':
            if not isinstance(result, collections.Iterable):
                raise ValueError(
                    'list_resource returned a non-iterable object')
            return map(self.make_url, result)
        else:
            return result

    def get_callback(self):
        if self.method == 'GET' and self.context.parameters:
            getall = 'getall' in self.context.parameters
            # remove ?getall= from GET examine other parameters
            filter = (len(self.context.parameters) - int(getall) and
                      hasattr(self.manager, self.METHOD_MAP['filter']))

            if getall and filter:
                self.method = 'getall+filter'
            elif getall:
                self.method = 'getall'
            elif filter:
                self.method = 'filter'
        return super(HTTPServiceCollectionRequest, self).get_callback()

    def call(self):
        if self.method == 'POST':
            return self.callback(self.data)
        elif 'filter' in self.method:
            return self.callback(self.context.parameters)
        else:
            return self.callback()
