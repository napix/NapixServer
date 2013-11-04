#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The Collections services handle the request on a specific manager.
"""

import sys

from napixd.services.urls import URL
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

    def __init__(self, collection, config, collection_url, namespace):
        self.collection = collection
        self.config = config
        self.namespace = namespace

        self.collection_url = collection_url
        self.resource_url = self.collection_url.add_variable()

        self.all_actions = [
            ActionService(self, action)
            for action in self.collection.get_all_actions()
        ]

        rf = self.collection._resource_fields
        self.resource_fields = dict(zip(rf, map(dict, rf.values())))
        self.meta_data = {
            'doc': (collection.__doc__ or '').strip(),
            'direct_plug': False if collection.get_managed_classes() else None,
            'views': dict((format_, (cb.__doc__ or '').strip())
                          for (format_, cb)
                          in self.collection.get_all_formats().items()),
            'managed_class': [mc.get_name()
                              for mc in self.collection.get_managed_classes()],
            'actions': dict((action.name, action.doc)
                            for action in self.all_actions),
            'collection_methods': ServiceCollectionRequest.available_methods(collection),
            'resource_methods': ServiceResourceRequest.available_methods(collection),
            'resource_fields': self.resource_fields,
            'source': {
                'class': self.collection.__name__,
                'module': self.collection.__module__,
                'file': sys.modules[self.collection.__module__].__file__,
            },
        }

    def generate_manager(self, resource):
        """
        instantiate a manager for the given resource
        """
        manager = self.collection(resource)
        manager.configure(self.config)
        return manager

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
        return ServiceResourceRequest(request, list(path), self).handle()

    def as_collection(self, request, *path):
        """
        Launches a request on this manager as a collection
        """
        return ServiceCollectionRequest(request, list(path), self).handle()

    def as_list_actions(self, request, *path):
        """
        Lists the :meth:`napixd.managers.actions.action`
        available on this manager.
        """
        return [x.name for x in self.all_actions]

    def as_managed_classes(self, request, *path):
        """
        Lists the :attr:`managed classes<napixd.managers.base.Manager.managed_class>`
        of this manager.
        """
        return ServiceManagedClassesRequest(request, list(path), self).handle()

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

    def get_name(self):
        return self.namespace

    def get_managers(self, path):
        raise NotImplementedError()


class FirstCollectionService(BaseCollectionService):
    """
    A specialisation of :class:`BaseCollectionService` used
    for the first level of managers.

    *namespace* is the :attr:`~napixd.loader.ManagerImport.alias`
    of the this manager.
    """

    def __init__(self, collection, config, namespace):
        super(FirstCollectionService, self).__init__(
            collection, config, URL([namespace]), namespace)
        self._cache = None

    def generate_manager(self):
        """
        Generates a manager.

        Keeps a cached version of the manager for a later use.
        The manager is reused if :meth:`napixd.managers.base.Manager.is_up_to_date`
        returns :obj:`True`
        """
        if self._cache is None or not self._cache.is_up_to_date():
            self._cache = super(
                FirstCollectionService, self).generate_manager(None)
        return self._cache

    def get_managers(self, path):
        return [], self.generate_manager()


class CollectionService(BaseCollectionService):
    """
    The subclass of :class:`BaseCollectionService` used
    for all the :class:`napixd.managers.base.Manager` classes
    after the first one.

    *previous_service* is the :class:`CollectionService` or the
    :class:`FirstCollectionService` of the parent manager.
    """

    def __init__(self, previous_service, managed_class, config, namespace):
        collection_url = previous_service.resource_url.add_segment(namespace)
        namespace = '{0}.{1}'.format(previous_service.get_name(), namespace)

        super(CollectionService, self).__init__(
            managed_class.manager_class, config, collection_url, namespace)
        self.extractor = managed_class.extractor
        self.previous_service = previous_service

    def generate_manager(self, resource):
        """
        instanciate a manager for the given resource
        """
        resource = self.extractor(resource)
        return super(CollectionService, self).generate_manager(resource)

    def get_managers(self, path):
        managers_list, manager = self.previous_service.get_managers(path[:-1])

        id_ = manager.validate_id(path[-1])
        resource = manager.get_resource(id_)
        wrapped = ResourceWrapper(manager, id_, resource)

        managers_list.append((manager, wrapped))

        # The manager for self is generated here.
        manager = self.generate_manager(wrapped)
        return managers_list, manager


class ActionService(object):
    """
    The Service class for :func:`napixd.managers.actions.action`

    *collection_service* is the :class:`BaseCollectionService`
    of the manager owning the action.
    *action_name* is the name of the action.
    """

    def __init__(self, collection_service, action_name):
        self.service = collection_service
        self.name = action_name
        self.action = getattr(collection_service.collection, action_name)
        self.doc = (self.action.__doc__ or '').strip()
        self.url = collection_service.resource_url.add_segment(
            '_napix_action').add_segment(self.name)
        rf = self.action.resource_fields
        self.resource_fields = dict(zip(rf, map(dict, rf.values())))

    def setup_bottle(self, app):
        app.route(unicode(self.url.add_segment('_napix_help')), self.as_help)
        app.route(unicode(self.url), self.as_action)

    def get_managers(self, path):
        return self.service.get_managers(path)

    def as_action(self, request, *path):
        return ServiceActionRequest(request, path, self, self.name).handle()

    def as_help(self, request, *path):
        """
        View for _napix_help
        """
        action = self.action
        return {
            'resource_fields': self.resource_fields,
            'doc': action.__doc__,
            'mandatory': action.mandatory,
            'optional': action.optional,
            'source': {
                'method': self.action.__name__,
                'class': self.service.collection.__name__,
                'module': self.service.collection.__module__,
                'file': sys.modules[self.service.collection.__module__].__file__,
            },
        }
