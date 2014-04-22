#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The Collections services handle the request on a specific manager.
"""

from napixd.services.requests import (
    ServiceCollectionRequest,
    ServiceManagedClassesRequest,
    ServiceResourceRequest,
    ServiceActionRequest
)
from napixd.services.contexts import CollectionContext

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

    Serve the *served_manager*.

    .. attribute:: collection_url

        The :class:`~napixd.services.urls.URL` where the
        requests on the collection are served

    .. attribute:: resource_url

        The :class:`~napixd.services.urls.URL` where the
        requests on the resource are served
    """

    def __init__(self, served_manager, url):
        self.served_manager = served_manager
        self.collection = served_manager.manager_class

        self.collection_url = url
        self.resource_url = self.collection_url.add_variable()
        self.lock = served_manager.lock

        self.all_actions = [
            ActionService(self, action)
            for action in served_manager.get_all_actions()
        ]

        self.resource_fields = served_manager.resource_fields
        self.meta_data = served_manager.meta_data

    def __repr__(self):
        return '{0} of {1}'.format(self.__class__.__name__,
                                   self.served_manager)

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

    def as_resource(self, napixd_context, *path):
        """
        Launches a request on a resource of this manager
        """
        return ServiceResourceRequest(CollectionContext(self, napixd_context), list(path)).handle()

    def as_collection(self, napixd_context, *path):
        """
        Launches a request on this manager as a collection
        """
        return ServiceCollectionRequest(CollectionContext(self, napixd_context), list(path)).handle()

    def as_list_actions(self, napixd_context, *path):
        """
        Lists the :meth:`napixd.managers.actions.action` available on this manager.
        """
        return [x.action for x in self.all_actions]

    def as_managed_classes(self, napixd_context, *path):
        """
        Lists the :attr:`managed classes<napixd.managers.Manager.managed_class>`
        of this manager.
        """
        return ServiceManagedClassesRequest(CollectionContext(self, napixd_context), list(path)).handle()

    def as_help(self, napixd_context, *path):
        """
        The view served at **_napix_help**
        """
        return self.meta_data

    def as_resource_fields(self, napixd_context, *path):
        """
        The view served at **_napix_resource_fields**
        """
        return self.resource_fields

    def as_example_resource(self, napixd_context, *path):
        """
        The view served at **_napix_help**
        """
        manager = self.collection
        return manager.get_example_resource()

    def noop(self, *args, **kw):
        """
        A catch-all method that does nothing but return a 200
        """
        return None

    def get_manager(self, resource, call_context):
        """
        Instantiates a manager for the given resource
        """
        return self.served_manager.instantiate(resource, call_context)


class FirstCollectionService(BaseCollectionService):
    """
    A specialisation of :class:`BaseCollectionService` used for the first level
    of managers.
    """

    def get_manager(self, path, call_context):
        assert not path
        return super(FirstCollectionService, self).get_manager(None, call_context)


class CollectionService(BaseCollectionService):
    """
    The subclass of :class:`BaseCollectionService` used for all the
    :class:`napixd.managers.base.Manager` classes after the first one.

    *previous_service* is the :class:`CollectionService` or the
    :class:`FirstCollectionService` of the parent manager.
    """

    def __init__(self, previous_service, served_manager, url):
        super(CollectionService, self).__init__(served_manager, url)
        self.previous_service = previous_service

    def get_manager(self, path, call_context):
        served_manager = self.previous_service.get_manager(path[:-1], call_context)

        served_manager.validate_id(path[-1])
        wrapped = served_manager.get_resource()

        # The manager for self is generated here.
        return super(CollectionService, self).get_manager(wrapped, call_context)


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

    def get_manager(self, path, call_context):
        return self.service.get_manager(path, call_context)

    def as_action(self, napixd_context, *path):
        return ServiceActionRequest(CollectionContext(self, napixd_context), path, self.action).handle()

    def as_help(self, napixd_context, *path):
        """
        View for _napix_help
        """
        return self.meta_data
