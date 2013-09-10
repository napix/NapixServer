#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from napixd.services.plugins import ArgumentsPlugin
from napixd.services.servicerequest import (
    ServiceCollectionRequest,
    ServiceManagedClassesRequest,
    ServiceResourceRequest,
    ServiceActionRequest
)


class BaseCollectionService(object):

    """
    Abstract class used by FirstCollectionService and CollectionService
    """

    collection_request_class = ServiceCollectionRequest
    resource_request_class = ServiceResourceRequest

    def __init__(self, previous_service, collection, config, namespace):
        """
        Serve the collection given as a managed class of the previous_service,
        with the config given.  collection is a subclass of Manager
        previous_service is an instance of CollectionService
        that serve the Manager class below.
        previous_service is None when it's the base collection being served.
        config is the instance of Conf for this Service.
        """
        self.previous_service = previous_service
        self.collection = collection
        self.config = config

        #Recursive list of services.
        self.services = list(self._services_stack())
        self.services.reverse()

        self.direct_plug = self.collection.direct_plug()
        #url is added if append_url is True
        self.url = namespace

        base_url = '/'
        last = len(self.services) - 1
        #build the prefix url with the list of previous services
        for i, service in enumerate(self.services):
            base_url += service.get_prefix()
            if i != last:
                base_url += ':f{0}/'.format(i)
        #collection and resource urls of this service
        self.collection_url = base_url
        self.resource_url = base_url + ':f%i' % last

        self.all_actions = [
            ActionService(self, action)
            for action in self.collection.get_all_actions()
        ]

        self.resource_fields = dict(self.collection._resource_fields)

    def get_name(self):
        return '.'.join(s.url for s in self.services)

    def get_prefix(self):
        """
        Get the prefix of this service
        if append_url was True, this service hasn't a prefix
        else, it's the url from the configuration
        ex:
        >>>cs = CollectionService(ps,ManagerClass,conf,namespace)
        >>>cs.get_prefix()
            'managerclass/'

        >>>cs = CollectionService(ps,ManagerClass,conf,namespace)
        >>>cs.get_prefix()
            ''
        """
        return self.url and self.url + '/' or ''

    def get_managers(self, path):
        raise NotImplementedError()

    def generate_manager(self, resource):
        """
        instanciate a manager for the given resource
        """
        manager = self.collection(resource)
        manager.configure(self.config)
        return manager

    def _services_stack(self):
        """
        return the list of services before this one
        """
        serv = self
        yield serv
        while serv.previous_service:
            yield serv.previous_service
            serv = serv.previous_service

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
        app.route(self.collection_url+'_napix_resource_fields',
                  callback=self.as_resource_fields,
                  method='GET',
                  apply=arguments_plugin)
        app.route(self.collection_url+'_napix_help',
                  callback=self.as_help,
                  method='GET',
                  apply=arguments_plugin)
        if hasattr(self.collection, 'create_resource'):
            app.route(self.collection_url+'_napix_new',
                      callback=self.as_example_resource,
                      method='GET',
                      apply=arguments_plugin)
        if self.all_actions:
            app.route(self.resource_url+'/_napix_all_actions',
                      callback=self.as_list_actions,
                      method='GET',
                      apply=arguments_plugin)
        for action in self.all_actions:
            action.setup_bottle(app)

        app.route(self.collection_url,
                  callback=self.as_collection,
                  method='ANY',
                  apply=arguments_plugin)
        app.route(self.resource_url,
                  callback=self.as_resource,
                  method='ANY',
                  apply=arguments_plugin)

        if self.direct_plug is False:
            app.route(self.resource_url+'/',
                      callback=self.as_managed_classes,
                      apply=arguments_plugin)
            for managed_class in self.collection.get_managed_classes():
                app.route(self.resource_url + '/' + managed_class.get_name(),
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


class FirstCollectionService(BaseCollectionService):
    def __init__(self, collection, config, namespace):
        super(FirstCollectionService, self).__init__(
            None, collection, config, namespace)
        self._cache = None

    def generate_manager(self):
        if self._cache is None or not self._cache.is_up_to_date():
            self._cache = super(FirstCollectionService, self).generate_manager(None)
        return self._cache

    def setup_bottle(self, app):
        # Nasty hack so /manager return a 200 response
        #even if it don't act like a resource
        app.route('/'+self.url, callback=self.noop)
        super(FirstCollectionService, self).setup_bottle(app)

    def get_managers(self, path):
        return [], self.generate_manager()


class CollectionService(BaseCollectionService):
    def __init__(self, previous_service, managed_class, config, namespace):
        super(CollectionService, self).__init__(
            previous_service, managed_class.manager_class, config, namespace)
        self.extractor = managed_class.extractor

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
        base_url = collection_service.resource_url
        self.name = action_name
        self.action = getattr(collection_service.collection, action_name)
        self.doc = (self.action.__doc__ or '').strip()
        self.url = '{0}/_napix_action/{1}'.format(base_url, self.name)
        self.resource_fields = dict(self.action.resource_fields)

    def setup_bottle(self, app):
        arguments_plugin = ArgumentsPlugin()
        app.route(self.url + '/_napix_help',
                  method='GET',
                  callback=self.as_help,
                  apply=arguments_plugin)
        app.route(self.url,
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
