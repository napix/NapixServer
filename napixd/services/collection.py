#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The Collections services handle the request on a specific manager.
"""

from napixd.services.wrapper import ResourceWrapper
from napixd.services.requests import (
    ServiceCollectionRequest,
    ServiceManagedClassesRequest,
    ServiceResourceRequest,
    ServiceActionRequest
)

__all__ = (
    'BaseCollectionService',
    'FirstCollectionService',
    'CollectionService',
    'ActionService'
)


class HTTPCollectionContext(object):
    def __init__(self, cs, request):
        self.service = cs
        self.request = request
        self.method = request.method
        self.parameters = request.GET
        self.data = request.data

    def get_managers(self, path):
        return self.service.get_managers(path, self.request)


class BaseCollectionService(object):
    """
    Abstract class used by :class:`FirstCollectionService` and
    :class:`CollectionService`

    Serve the *collection* with the given *config*.
    *collection* is a subclass of :class:`~napixd.managers.base.Manager`
    *config* is the instance of :class:`napixd.conf.Conf`.
    *collection_url* is an :class:`napixd.services.urls.URL` where the service
    is listening.

    .. attribute:: collection_url

        The :class:`~napixd.services.urls.URL` where the
        requests on the collection are served

    .. attribute:: resource_url

        The :class:`~napixd.services.urls.URL` where the
        requests on the resource are served
    """

    def __init__(self, served_manager):
        self.served_manager = served_manager
        self.collection = served_manager.manager_class

        self.collection_url = served_manager.url
        self.resource_url = self.collection_url.add_variable()
        self.lock = served_manager.lock

        self.all_actions = [
            ActionService(self, action)
            for action in served_manager.get_all_actions()
        ]

        self.resource_fields = served_manager.resource_fields
        self.meta_data = served_manager.meta_data

    def _generate_manager(self, resource, request):
        """
        instantiate a manager for the given resource
        """
        return self.served_manager.instantiate(resource, request)

    def setup_bottle(self, app):
        """
        Register the routes of this collection inside the app

        collection/
            list the collection
        collection/_napix_new
            New object template
        collection/_napix_help
            collection complete documentation
        collection/_napix_resource_fields
            collection resource files documentation

        collection/resource
            Get the specified resource
        collection/resource/_napix_all_actions
            All actions of the resource

        collection/resource/_napix_action/action
            Call the action on the resource
        collection/resource/_napix_action/action/_napix_help
            documentation of the action
        """
        app.route(
            unicode(self.collection_url.add_segment('_napix_resource_fields')),
            self.as_resource_fields)
        app.route(
            unicode(self.collection_url.add_segment('_napix_help')),
            self.as_help)
        if hasattr(self.collection, 'create_resource'):
            app.route(
                unicode(self.collection_url.add_segment('_napix_new')),
                self.as_example_resource)
        if self.all_actions:
            app.route(
                unicode(self.resource_url.add_segment('_napix_all_actions')),
                self.as_list_actions)
        for action in self.all_actions:
            action.setup_bottle(app)

        app.route(unicode(self.collection_url), self.noop)
        app.route(self.collection_url.with_slash(), self.as_collection)
        app.route(unicode(self.resource_url), self.as_resource)

        if self.collection.get_managed_classes():
            app.route(self.resource_url.with_slash(), self.as_managed_classes)

    def as_resource(self, request, *path):
        """
        Launches a request on a resource of this manager
        """
        return ServiceResourceRequest(HTTPCollectionContext(self, request), list(path)).handle()

    def as_collection(self, request, *path):
        """
        Launches a request on this manager as a collection
        """
        return ServiceCollectionRequest(HTTPCollectionContext(self, request), list(path)).handle()

    def as_list_actions(self, request, *path):
        """
        Lists the :meth:`napixd.managers.actions.action`
        available on this manager.
        """
        return [x.action for x in self.all_actions]

    def as_managed_classes(self, request, *path):
        """
        Lists the :attr:`managed classes<napixd.managers.base.Manager.managed_class>`
        of this manager.
        """
        return ServiceManagedClassesRequest(HTTPCollectionContext(self, request), list(path)).handle()

    def as_help(self, request, *path):
        """
        The view server at **_napix_help**
        """
        return self.meta_data

    def as_resource_fields(self, request, *path):
        """
        The view server at **_napix_resource_fields**
        """
        return self.resource_fields

    def as_example_resource(self, request, *path):
        """
        The view server at **_napix_help**
        """
        manager = self.collection
        return manager.get_example_resource()

    def noop(self, **kw):
        """
        A catch-all method that does nothing but return a 200
        """
        return None

    def get_managers(self, path, request):
        raise NotImplementedError()


class FirstCollectionService(BaseCollectionService):
    """
    A specialisation of :class:`BaseCollectionService` used
    for the first level of managers.

    *namespace* is the :attr:`~napixd.loader.ManagerImport.alias`
    of the this manager.
    """

    def get_managers(self, path, request):
        return [], self._generate_manager(None, request)


class CollectionService(BaseCollectionService):
    """
    The subclass of :class:`BaseCollectionService` used
    for all the :class:`napixd.managers.base.Manager` classes
    after the first one.

    *previous_service* is the :class:`CollectionService` or the
    :class:`FirstCollectionService` of the parent manager.
    """

    def __init__(self, previous_service, served_manager):
        super(CollectionService, self).__init__(served_manager)
        self.extractor = served_manager.extractor
        self.previous_service = previous_service

    def _generate_manager(self, resource, request):
        """
        instanciate a manager for the given resource
        """
        resource = self.extractor(resource)
        return super(CollectionService, self)._generate_manager(resource, request)

    def get_managers(self, path, request):
        managers_list, manager = self.previous_service.get_managers(path[:-1], request)

        id_ = manager.validate_id(path[-1])
        resource = manager.get_resource(id_)
        wrapped = ResourceWrapper(manager, id_, resource)

        managers_list.append((manager, wrapped))

        # The manager for self is generated here.
        manager = self._generate_manager(wrapped, request)
        return managers_list, manager


class ActionService(object):
    """
    The Service class for :func:`napixd.managers.actions.action`

    *collection_service* is the :class:`BaseCollectionService`
    of the manager owning the action.
    *action_name* is the name of the action.
    """

    def __init__(self, collection_service, served_action):
        self.service = collection_service
        self.action = served_action.name
        self.url = self.service.resource_url.add_segment('_napix_action').add_segment(served_action.name)
        self.meta_data = served_action.meta_data
        self.lock = served_action.lock

    def setup_bottle(self, app):
        app.route(unicode(self.url.add_segment('_napix_help')), self.as_help)
        app.route(unicode(self.url), self.as_action)

    def get_managers(self, path, request):
        return self.service.get_managers(path, request)

    def as_action(self, request, *path):
        return ServiceActionRequest(HTTPCollectionContext(self, request), path, self.action).handle()

    def as_help(self, request, *path):
        """
        View for _napix_help
        """
        return self.meta_data
