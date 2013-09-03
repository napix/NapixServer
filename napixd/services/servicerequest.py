#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import bottle

from napixd.http import Response
from napixd.exceptions import NotFound, ValidationError, Duplicate
from napixd.services.methods import Implementation


class ServiceRequest(object):
    """
    ServiceRequest is an abstract class created to serve a single request.
    """
    def __init__(self, path, service):
        """
        Create the object that will handle the request for the path given
        on the collection
        """
        self.method = bottle.request.method
        self.service = service
        #Parse the url components
        self.path = map(urllib.unquote, path)

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

    def check_datas(self, for_edit=False):
        """
        Filter and check the collection fields.

        Remove any field that is not in the collection's field
        Call the validator of the collection
        """
        if self.method not in ('POST', 'PUT'):
            return {}
        data = self.manager.unserialize(bottle.request.data)
        return self.manager.validate(data, for_edit=for_edit)

    def get_manager(self):
        """
        Retreive the manager associated with the current request
        """
        self.all_managers, manager = self.service.get_managers(self.path)
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
            raise bottle.HTTPError(
                405, 'Method is not implemented',
                allow=','.join(self.available_methods(self.manager)))

    def call(self):
        """
        Make the actual call of the method
        """
        raise NotImplementedError

    def start_request(self):
        for m, i, r in self.all_managers:
            m.start_request(bottle.request)
            m.start_managed_request(bottle.request, i, r)
        self.manager.start_request(bottle.request)

    def end_request(self):
        self.manager.end_request(bottle.request)
        for m, i, r in reversed(self.all_managers):
            m.end_managed_request(bottle.request, i, r)
            m.end_request(bottle.request)

    def serialize(self, result):
        return result

    def handle(self):
        """
        Actually handle the request.
        Call a set of methods that may be overrident by subclasses
        """
        try:
            #obtient l'object designé
            self.manager = self.get_manager()
            self.start_request()

            #recupère la vue qui va effectuer la requete
            self.callback = self.get_callback()
            #recupère les données valides pour cet objet
            self.data = self.check_datas()
            #recupere les arguments a passer a cette vue
            result = self.call()

            self.end_request()
            return self.serialize(result)
        except ValidationError, e:
            raise bottle.HTTPError(400, dict(e))
        except NotFound, e:
            raise bottle.HTTPError(404, '`{0}` not found'.format(unicode(e)))
        except Duplicate, e:
            raise bottle.HTTPError(409, '`{1}` already exists'.format(
                unicode(e) or 'object'))

    def make_url(self, result):
        """
        Create an url for the *list* **result**.
        The url follow the services prefix
        """
        url = ['']
        path = list(self.path)
        path.append(result)
        services = (s.url for s in self.service.services)
        for id_ in path:
            prefix = next(services, '')
            if prefix:
                url.append(prefix)
            url.append(urllib.quote(str(id_), ''))
        return '/'.join(url)


class ServiceCollectionRequest(ServiceRequest):
    """
    ServiceCollectionRequest is an implementation of ServiceRequest specified
    for Collection requests (urls ending with /)
    """
    #association de verbes HTTP aux methodes python
    METHOD_MAP = {
        'filter': 'list_resource_filter',
        'getall': 'get_all_resources',
        'getall+filter': 'get_all_resources_filter',
        'POST': 'create_resource',
        'GET': 'list_resource',
        'HEAD': 'list_resource'
        }

    def get_manager(self):
        manager = super(ServiceCollectionRequest, self).get_manager()
        return Implementation(manager)

    def get_callback(self):
        if (self.method == 'GET' and bottle.request.GET):
            getall = 'getall' in bottle.request.GET
            #remove ?getall= from GET examine other parameters
            filter = (len(bottle.request.GET) - int(getall) and
                      hasattr(self.manager, self.METHOD_MAP['filter']))

            if getall and filter:
                self.method = 'getall+filter'
            elif getall:
                self.method = 'getall'
            elif filter:
                self.method = 'filter'
        return super(ServiceCollectionRequest, self).get_callback()

    def check_datas(self):
        return super(ServiceCollectionRequest, self).check_datas(for_edit=False)

    def call(self):
        if self.method == 'POST':
            return self.callback(self.data)
        elif 'filter' in self.method:
            return self.callback(bottle.request.GET)
        else:
            return self.callback()

    def serialize(self, result):
        if self.method == 'HEAD':
            return None
        elif self.method == 'POST':
            url = self.make_url(result)
            return bottle.HTTPError(201, None, Location=url)
        elif self.method == 'GET' or self.method == 'filter':
            return map(self.make_url, result)
        else:
            return result


class ServiceManagedClassesRequest(ServiceRequest):

    def get_callback(self):
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
            if result is not None and result != self.resource_id:
                new_url = self.make_url(result)
                return bottle.HTTPError(205, None, Location=new_url)
            return bottle.HTTPError(204)
        if self.method != 'GET':
            return result
        format_ = bottle.request.GET.get('format', None)
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
            return bottle.HTTPError(406, message)

        response = Response()
        result = formatter(self.resource_id, result, response)
        if result is None or result is response:
            return response
        else:
            return bottle.HTTPResponse(result, header=response.headers)

    def default_formatter(self, value):
        resp = self.manager.serialize(value)
        return resp

    def call(self):
        if self.method == 'PUT':
            return self.callback(self.resource_id, self.data)
        else:
            return self.callback(self.resource_id)

    def get_manager(self):
        #get the last path token because we may not just want to GET the resource
        resource_id = self.path.pop()
        manager = super(ServiceResourceRequest, self).get_manager()
        #verifie l'identifiant de la resource aussi
        self.resource_id = manager.validate_id(resource_id)
        return manager

    def check_datas(self):
        return super(ServiceResourceRequest, self).check_datas(for_edit=True)


class ServiceActionRequest(ServiceResourceRequest):
    METHOD_MAP = {
        'POST': 'get_resource',
        }

    def __init__(self, path, service, action_name):
        self.action_name = action_name
        super(ServiceActionRequest, self).__init__(path, service)

    def get_callback(self):
        self.resource = self.manager.get_resource(self.resource_id)
        return getattr(self.manager, self.action_name)

    def check_datas(self):
        callback = getattr(self.manager, self.action_name)
        data = callback.resource_fields.validate(bottle.request.data)
        return data

    def call(self):
        return self.callback(self.resource, **self.data)
