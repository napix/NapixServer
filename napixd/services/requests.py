#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The services instanciate a instance of a :class:`ServiceRequest` sub-class
to handle the specific work of a request.
"""

import collections

from napixd.http.response import Response, HTTPError, HTTPResponse, HTTP405
from napixd.exceptions import NotFound, ValidationError, Duplicate
from napixd.services.methods import Implementation
from napixd.services.wrapper import ResourceWrapper


__all__ = (
    'ServiceRequest',
    'ServiceResourceRequest',
    'ServiceCollectionRequest',
    'ServiceManagedClassesRequest',
    'ServiceActionRequest',
)


class ServiceRequest(object):
    """
    This class is an abstract class created to serve a single request.

    The object handles the request for the *path* given on the *service*.
    *service* is an instance of
    :class:`napixd.services.collection.CollectionService`.
    """

    def __init__(self, request, path, service):
        self.request = request
        self.method = request.method
        self.service = service
        # Parse the url components
        self.path = list(path)
        self.lock = service.lock

    @classmethod
    def available_methods(cls, manager):
        """
        Return the HTTP methods defined in the given manager
        that are usable with this ServiceRequest
        """
        available_methods = []
        for meth, callback in cls.METHOD_MAP.items():
            if meth.isupper() and hasattr(manager, callback):
                available_methods.append(meth)
        return available_methods

    def check_datas(self):
        """
        Filter and check the collection fields.

        Remove any field that is not in the collection's field
        Call the validator of the collection
        """
        return {}

    def get_manager(self, path=None):
        """
        Retreive the manager associated with the current request
        """
        self.all_managers, manager = self.service.get_managers(
            self.path if path is None else path, self.request)
        return manager

    def get_callback(self):
        """
        Retreive the method we'll call using self.METHOD_MAP and the user input
        (ie the HTTP method used on the ressource)

        Return 405 if the request is not implemented.
        """
        try:
            return getattr(self.manager, self.METHOD_MAP[self.method])
        except (AttributeError, KeyError):
            raise HTTP405(self.available_methods(self.manager))

    def call(self):
        """
        Make the actual call of the method
        """
        raise NotImplementedError

    def start_request(self):
        for manager, wrapper in self.all_managers:
            manager.start_request(self.request)
            manager.start_managed_request(self.request, wrapper)
        self.manager.start_request(self.request)

    def end_request(self):
        self.manager.end_request(self.request)
        for manager, wrapper in reversed(self.all_managers):
            manager.end_managed_request(self.request, wrapper)
            manager.end_request(self.request)

    def serialize(self, result):
        """
        Serialize the *result* into something meaningful.

        This has to be implemented by the subclasses.
        """
        raise NotImplementedError()

    def handle(self):
        """
        Actually handle the request.
        Call a set of methods that may be overrident by subclasses.
        """
        if self.lock is not None:
            self.lock.acquire()

        try:
            # obtient l'object designé
            self.manager = self.get_manager()
            self.start_request()

            # recupère la vue qui va effectuer la requete
            self.callback = self.get_callback()
            # recupère les données valides pour cet objet
            self.data = self.check_datas()
            # recupere les arguments a passer a cette vue
            result = self.call()

            self.end_request()
            return self.serialize(result)
        except ValidationError, e:
            raise HTTPError(400, dict(e))
        except NotFound, e:
            raise HTTPError(404, '`{0}` not found'.format(unicode(e)))
        except Duplicate, e:
            raise HTTPError(409, '`{0}` already exists'.format(
                unicode(e) or 'object'))
        finally:
            if self.lock is not None:
                self.lock.release()

    def make_url(self, result):
        """
        Creates an url for the *list* **result**.
        """
        path = list(self.path)
        path.append(result)

        return self.service.resource_url.reverse(path)


class ServiceCollectionRequest(ServiceRequest):
    """
    ServiceCollectionRequest is an implementation of :class:`ServiceRequest`
    specialized for Collection requests (urls ending with /)
    """
    # association de verbes HTTP aux methodes python
    METHOD_MAP = {
        'filter': 'list_resource_filter',
        'getall': 'get_all_resources',
        'getall+filter': 'get_all_resources_filter',
        'POST': 'create_resource',
        'GET': 'list_resource',
        'HEAD': 'list_resource'
    }

    def get_manager(self):
        """
        Returns an :class:`napixd.services.methods.Implementation`
        of the manager.
        """
        manager = super(ServiceCollectionRequest, self).get_manager()
        return Implementation(manager)

    def get_callback(self):
        if (self.method == 'GET' and self.request.GET):
            getall = 'getall' in self.request.GET
            # remove ?getall= from GET examine other parameters
            filter = (len(self.request.GET) - int(getall) and
                      hasattr(self.manager, self.METHOD_MAP['filter']))

            if getall and filter:
                self.method = 'getall+filter'
            elif getall:
                self.method = 'getall'
            elif filter:
                self.method = 'filter'
        return super(ServiceCollectionRequest, self).get_callback()

    def check_datas(self):
        if self.method != 'POST':
            return super(ServiceCollectionRequest, self).check_datas()

        data = self.request.data
        return self.manager.validate(data, None)

    def call(self):
        if self.method == 'POST':
            return self.callback(self.data)
        elif 'filter' in self.method:
            return self.callback(self.request.GET)
        else:
            return self.callback()

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


class ServiceManagedClassesRequest(ServiceRequest):
    """
    The ServiceRequest class for the listing of the managed classes
    of a manager.
    """

    def get_manager(self):
        resource_id = self.path[-1]
        manager = super(ServiceManagedClassesRequest, self).get_manager(
            path=self.path[:-1])
        # verifie l'identifiant de la resource aussi
        self.resource_id = manager.validate_id(resource_id)
        return manager

    def get_callback(self):
        if not (self.method == 'GET' or self.method == 'HEAD'):
            raise HTTP405(['GET', 'HEAD'])
        self.manager.get_resource(self.resource_id)
        return self.service.collection.get_managed_classes

    def call(self):
        return self.callback()

    def serialize(self, result):
        return [self.make_url(mc.get_name()) for mc in result]


class ServiceResourceRequest(ServiceRequest):

    """
    ServiceResourceRequest is an implementation of ServiceRequest specified for
    Ressource requests (urls not ending with /)
    """
    METHOD_MAP = {
        'PUT': 'modify_resource',
        'GET': 'get_resource',
        'HEAD': 'get_resource',
        'DELETE': 'delete_resource',
    }

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

        format_ = self.request.GET.get('format', None)
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

    def call(self):
        if self.method == 'PUT':
            return self.callback(self.resource, self.data)
        elif self.method in ('GET', 'HEAD'):
            return self.resource.resource
        else:
            return self.callback(self.resource)

    def get_manager(self):
        # get the last path token because we may not just want to GET the
        # resource
        resource_id = self.path.pop()
        manager = super(ServiceResourceRequest, self).get_manager()
        # verifie l'identifiant de la resource aussi
        resource_id = manager.validate_id(resource_id)
        resource = manager.get_resource(resource_id)

        self.resource = ResourceWrapper(manager, resource_id, resource)
        return manager

    def check_datas(self):
        if self.method != 'PUT':
            return super(ServiceResourceRequest, self).check_datas()

        data = self.request.data
        return self.manager.validate(data, self.resource.resource)


class ServiceActionRequest(ServiceResourceRequest):
    METHOD_MAP = {
        'POST': 'get_resource',
    }

    def __init__(self, request, path, service, action_name):
        super(ServiceActionRequest, self).__init__(request, path, service)
        self.action_name = action_name

    def check_datas(self):
        callback = getattr(self.manager, self.action_name)
        data = callback.resource_fields.validate(self.request.data)
        return data

    def get_callback(self):
        return getattr(self.manager, self.action_name)

    def call(self):
        return self.callback(self.resource, **self.data)
