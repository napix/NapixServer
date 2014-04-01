#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections

from napixd.services.requests.base import ServiceRequest
from napixd.services.requests.http import HTTPMixin, MethodMixin
from napixd.http.response import HTTPError, Response, HTTPResponse


class ServiceResourceRequest(ServiceRequest):

    """
    ServiceResourceRequest is an implementation of ServiceRequest specified for
    Resource requests (urls not ending with /)
    """

    def get_manager(self):
        # get the last path token because we may not just want to GET the
        # resource
        resource_id = self.path.pop()
        manager = super(ServiceResourceRequest, self).get_manager()

        # verifie l'identifiant de la resource aussi
        resource_id = manager.validate_id(resource_id)

        self.resource = manager.get_resource(resource_id)
        return manager


class ModifyResourceMixin(object):
    def check_datas(self):
        data = self.context.data
        return self.manager.validate(data, self.resource.resource)


class HTTPServiceResourceRequest(ModifyResourceMixin, MethodMixin, HTTPMixin, ServiceResourceRequest):
    METHOD_MAP = {
        'PUT': 'modify_resource',
        'GET': 'get_resource',
        'HEAD': 'get_resource',
        'DELETE': 'delete_resource',
    }

    def check_datas(self):
        if self.method == 'PUT':
            return super(HTTPServiceResourceRequest, self).check_datas()
        return super(ModifyResourceMixin, self).check_datas()

    def call(self):
        if self.method == 'PUT':
            return self.callback(self.resource, self.data)
        elif self.method in ('GET', 'HEAD'):
            return self.resource.resource
        else:
            return self.callback(self.resource)

    def serialize(self, result):
        if self.method == 'HEAD':
            return None
        if self.method == 'PUT':
            if result is not None and result != self.resource.id:
                new_url = self.make_url(result)
                return HTTPError(205, None, Location=new_url)
            return HTTPError(204)

        if self.method != 'GET':
            return result

        if result is None:
            raise ValueError('resource cannot be None')

        format_ = self.context.parameters.get('format', None)
        if not format_:
            return self.default_formatter(result)
        try:
            formatter = self.manager.get_formatter(format_)
        except KeyError:
            message = 'Cannot render %s.' % format_
            all_formats = self.service.collection.get_all_formats()
            if all_formats:
                message = '{0} Available formats {1}: {2} '.format(
                    message, 'is' if len(all_formats) <= 1 else 'are',
                    ', '.join(all_formats.keys()))
            return HTTPError(406, message)

        response = Response()
        result = formatter(self.resource, response)
        if result is None or result is response:
            return response
        else:
            return HTTPResponse(response.headers, result)

    def default_formatter(self, value):
        resp = self.manager.serialize(value)
        if not isinstance(resp, collections.Mapping):
            raise ValueError('Serialized value is not an dict')
        return resp


class ServiceActionRequest(ServiceResourceRequest):

    def __init__(self, context, path, action_name):
        super(ServiceActionRequest, self).__init__(context, path)
        self.action_name = action_name

    def check_datas(self):
        data = self.callback.resource_fields.validate(self.context.data)
        return data

    def get_callback(self):
        return getattr(self.manager, self.action_name)

    def call(self):
        return self.callback(self.resource, **self.data)


class HTTPServiceActionRequest(HTTPMixin, ServiceActionRequest):
    METHOD_MAP = {
        'POST': 'get_resource',
    }

    def serialize(self, r):
        return r


class FetchResource(ServiceResourceRequest):
    def get_callback(self):
        return None

    def call(self):
        return self.resource
