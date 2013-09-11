#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from napixd.services.urls import URL
from napixd.services.plugins import ArgumentsPlugin
from napixd.services.service_requests import (
    ServiceCollectionRequest,
    ServiceManagedClassesRequest,
    ServiceResourceRequest,
    ServiceActionRequest
)


class BaseCollectionService(object):
    """
    Abstract class used by FirstCollectionService and CollectionService
    """

    def __init__(self, collection, config, collection_url):
        """
        Serve the collection with the config given.
        collection is a subclass of Manager
        config is the instance of Conf for this Service.
        """
        self.collection = collection
        self.config = config

        self.direct_plug = self.collection.direct_plug()
        #url is added if append_url is True

        self.collection_url = collection_url
        self.resource_url = self.collection_url.add_variable()

        self.all_actions = [
            ActionService(self, action)
            for action in self.collection.get_all_actions()
        ]

        self.resource_fields = dict(self.collection._resource_fields)

    def generate_manager(self, resource):
        """
        instanciate a manager for the given resource
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
        arguments_plugin = ArgumentsPlugin()
        app.route(
            unicode(self.collection_url.add_segment('_napix_resource_fields')),
            callback=self.as_resource_fields,
            method='GET',
            apply=arguments_plugin)
        app.route(
            unicode(self.collection_url.add_segment('_napix_help')),
            callback=self.as_help,
            method='GET',
            apply=arguments_plugin)
        if hasattr(self.collection, 'create_resource'):
            app.route(
                unicode(self.collection_url.add_segment('_napix_new')),
                callback=self.as_example_resource,
                method='GET',
                apply=arguments_plugin)
        if self.all_actions:
            app.route(
                unicode(self.resource_url.add_segment('_napix_all_actions')),
                callback=self.as_list_actions,
                method='GET',
                apply=arguments_plugin)
        for action in self.all_actions:
            action.setup_bottle(app)

        app.route(self.collection_url.with_slash(),
                  callback=self.as_collection,
                  method='ANY',
                  apply=arguments_plugin)
        app.route(unicode(self.resource_url),
                  callback=self.as_resource,
                  method='ANY',
                  apply=arguments_plugin)

        if self.direct_plug is False:
            app.route(self.resource_url.with_slash(),
                      callback=self.as_managed_classes,
                      apply=arguments_plugin)
            for managed_class in self.collection.get_managed_classes():
                app.route(
                    unicode(self.resource_url.add_segment(managed_class.get_name())),
                    callback=self.noop)

    def as_resource(self, path):
        return ServiceResourceRequest(path, self).handle()

    def as_collection(self, path):
        return ServiceCollectionRequest(path, self).handle()

    def as_list_actions(self, path):
        return [x.name for x in self.all_actions]

    def as_managed_classes(self, path):
        return ServiceManagedClassesRequest(path, self).handle()

    def as_help(self, path):
        manager = self.collection
        return {
            'doc': (manager.__doc__ or '').strip(),
            'direct_plug': self.direct_plug,
            'views': dict((format_, (cb.__doc__ or '').strip())
                          for (format_, cb)
                          in self.collection.get_all_formats().items()),
            'managed_class': [mc.get_name()
                              for mc in self.collection.get_managed_classes()],
            'actions': dict((action.name, action.doc)
                            for action in self.all_actions),
            'collection_methods': ServiceCollectionRequest.available_methods(manager),
            'resource_methods': ServiceResourceRequest.available_methods(manager),
            'resource_fields': self.resource_fields,
            'source': {
                'class': self.collection.__name__,
                'module': self.collection.__module__,
                'file': sys.modules[self.collection.__module__].__file__,
            },
        }

    def as_resource_fields(self, path):
        return self.resource_fields

    def as_example_resource(self, path):
        manager = self.collection
        return manager.get_example_resource()

    def noop(self, **kw):
        return None

    def get_name(self):
        raise NotImplementedError()

    def get_managers(self, path):
        raise NotImplementedError()


class FirstCollectionService(BaseCollectionService):
    def __init__(self, collection, config, namespace):
        super(FirstCollectionService, self).__init__(
            collection, config, URL([namespace]))
        self._cache = None
        self.namespace = namespace

    def generate_manager(self):
        if self._cache is None or not self._cache.is_up_to_date():
            self._cache = super(FirstCollectionService, self).generate_manager(None)
        return self._cache

    def setup_bottle(self, app):
        # Nasty hack so /manager return a 200 response
        #even if it don't act like a resource
        app.route(unicode(self.collection_url), callback=self.noop)
        super(FirstCollectionService, self).setup_bottle(app)

    def get_managers(self, path):
        return [], self.generate_manager()

    def get_name(self):
        return self.namespace


class CollectionService(BaseCollectionService):
    def __init__(self, previous_service, managed_class, config, namespace):
        if namespace:
            collection_url = previous_service.resource_url.add_segment(namespace)
        else:
            collection_url = previous_service.resource_url

        super(CollectionService, self).__init__(
            managed_class.manager_class, config, collection_url)
        self.extractor = managed_class.extractor
        self.previous_service = previous_service

        self.namespace = '{0}.{1}'.format(
            self.previous_service.get_name(), namespace)
        #collection and resource urls of this service

    def get_name(self):
        return self.namespace

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

        managers_list.append((manager, id_, resource))

        #The manager for self is generated here.
        manager = self.generate_manager(resource)
        return managers_list, manager


class ActionService(object):
    def __init__(self, collection_service, action_name):
        self.service = collection_service
        self.name = action_name
        self.action = getattr(collection_service.collection, action_name)
        self.doc = (self.action.__doc__ or '').strip()
        self.url = collection_service.resource_url.add_segment(
            '_napix_action').add_segment(self.name)
        self.resource_fields = dict(self.action.resource_fields)

    def setup_bottle(self, app):
        arguments_plugin = ArgumentsPlugin()
        app.route(
            unicode(self.url.add_segment('_napix_help')),
            method='GET',
            callback=self.as_help,
            apply=arguments_plugin)
        app.route(
            unicode(self.url),
            method='POST',
            callback=self.as_action,
            apply=arguments_plugin)

    def get_managers(self, path):
        return self.service.get_managers(path)

    def as_action(self, path):
        return ServiceActionRequest(path, self, self.name).handle()

    def as_help(self, path):
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
