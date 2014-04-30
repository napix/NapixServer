#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections

from napixd.exceptions import InternalRequestFailed, NotFound, ValidationError
from napixd.services.requests.base import ServiceRequest
from napixd.services.requests.http import HTTPMixin, MethodMixin
from napixd.http.response import HTTPError, Response, HTTPResponse, HTTP405


class ServiceResourceRequest(ServiceRequest):
    """
    :class:`ServiceResourceRequest` is an implementation of :class:`ServiceRequest`
    specified for Resource requests (urls not ending with /)

    All requests must be on an existing (returned by :meth:`napixd.managers.Manager.get_resource`).
    """

    def get_manager(self):
        """
        Get the manager and set :attr:`resource` to the :class:`napixd.services.wrapper.ResourceWrapper`.
        """
        # get the last path token because we may not just want to GET the
        # resource
        resource_id = self.path[-1]
        served_manager = super(ServiceResourceRequest, self).get_manager(self.path[:-1])

        # verifie l'identifiant de la resource aussi
        resource_id = served_manager.validate_id(resource_id)

        self.resource = served_manager.get_resource()
        return served_manager.manager


class ModifyResourceMixin(object):
    """
    A mixin for :class:`ServiceResourceRequest` that intents to call
    :meth:`napixd.managers.Manager.modify_resource`.
    """
    def check_datas(self):
        """"
        Use :meth:`napixd.managers.Manager.validate` for the valition
        of the data.
        """
        data = self.context.data
        return self.manager.validate(data, self.resource.resource)


class HTTPServiceResourceRequest(ModifyResourceMixin, MethodMixin, HTTPMixin, ServiceResourceRequest):
    """
    :class:`ServiceResourceRequest` sub class for the handling of requests coming from the HTTP server.
    """
    METHOD_MAP = {
        'PUT': 'modify_resource',
        'GET': 'get_resource',
        'HEAD': 'get_resource',
        'DELETE': 'delete_resource',
    }

    def check_datas(self):
        """
        Uses :meth:`ModifyResourceMixin.check_datas` for PUT request.
        """
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
        """
        Serialize the request.

        Also applies the *format* if asked in the parameters.
        """
        if self.method == 'HEAD':
            return None
        if self.method == 'PUT':
            if result is not None and result != self.resource.id:
                self.path.pop()
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
        """
        The default formatter is :meth:`napixd.managers.Manager.serialize`.

        The method also ensures that the serialized value is a :class:`collections.Mapping`.
        """
        resp = self.manager.serialize(value)
        if not isinstance(resp, collections.Mapping):
            print resp
            raise ValueError('Serialized value is not a dict')
        return resp


class ServiceActionRequest(ServiceResourceRequest):
    """
    :class:`ServiceResourceRequest` used to call :mod:`napixd.managers.actions`
    on a resource.
    """
    def __init__(self, context, path, action_name):
        super(ServiceActionRequest, self).__init__(context, path)
        self.action_name = action_name

    def check_datas(self):
        """
        Checks the data with the :attr:`~napixd.managers.actions.BoundAction.resource_fields`
        """
        data = self.callback.resource_fields.validate(self.context.data)
        return data

    def get_callback(self):
        """
        Returns the :class:`~napixd.managers.actions.BoundAction` from the :class:`napixd.managers.Manager`.
        """
        return getattr(self.manager, self.action_name)

    def call(self):
        return self.callback(self.resource, **self.data)


class HTTPServiceActionRequest(HTTPMixin, ServiceActionRequest):
    """
    :class:`ServiceActionRequest` for the HTTP requests.
    """
    METHOD_MAP = {
        'POST': 'get_resource',
    }

    def serialize(self, r):
        return r


class FetchResource(ServiceResourceRequest):
    """
    :class:`ServiceResourceRequest` for the internal request passed through
    :meth:`napixd.services.contexts.CollectionContext.get_resource`.
    """
    def get_callback(self):
        return None

    def call(self):
        try:
            return self.resource
        except (ValidationError, NotFound) as e:
            raise InternalRequestFailed(e)


class HTTPServiceManagedClassesRequest(HTTPMixin, ServiceResourceRequest):
    """
    The :class:`ServiceRequest` class for the listing of the managed classes
    of a manager.
    """

    def get_callback(self):
        if not (self.context.method == 'GET' or self.context.method == 'HEAD'):
            raise HTTP405(['GET', 'HEAD'])
        return self.service.collection.get_managed_classes

    def call(self):
        return self.callback()

    def serialize(self, result):
        """
        Creates urls for the managed classes aliases.
        """
        return [self.make_url(mc.get_name()) for mc in result]
