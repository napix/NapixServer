#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The service class is the interface between the managers and the web server

The service plug itself in the url router of Bottle, and will instantiate the
appropriate Napix Manager to handle the request.
"""

import logging

from napixd.exceptions import InternalRequestFailed
from napixd.services.urls import URL
from napixd.services.collection import (
    FirstCollectionService,
    CollectionService
)
from napixd.services.lock import LockFactory
from napixd.services.served import (
    FirstServedManager,
    ServedManager,
)


logger = logging.getLogger('Napix.service')

MAX_LEVEL = 5
lock_factory = LockFactory()


class Service(object):

    """
    The service objects make the interface between
    the end user's HTTP calls and the active modules.
    """

    def __init__(self, collection, namespace, configuration):
        """
        Create a base service for the given collection (a Manager object) and
        its submanager.
        *namespace* is the manager name (could be forced in conf)
        configuration parameters is the manager's config read from config file
        FIXME : remplacer collection par manager dans le code PARTOUT
        collection MUST be a Manager subclass and
        configuration an instance of Conf for this collection
        """
        self.configuration = configuration
        self._collection_services = {}
        self.url = URL([namespace])

        if 'Lock' in configuration:
            lock_conf = configuration.get('Lock')
            if not 'name' in lock_conf:
                raise ValueError('Lock configuration must have at least a name')

            logger.info('Creating lock %s for %s', lock_conf.get('name'), namespace)
            self.lock = lock_factory(lock_conf)
        else:
            self.lock = None

        namespaces = (namespace, )
        service = FirstCollectionService(
            FirstServedManager(
                collection,
                self.configuration,
                self.url,
                namespaces,
                lock=self.lock,
            ))

        self._collection_services[namespaces] = service
        self.create_collection_service(collection, namespaces, service, 0)

    def get_collection_service(self, aliases):
        try:
            return self._collection_services[tuple(aliases)]
        except KeyError:
            raise InternalRequestFailed('There is no collection service "{0}" in this service.'.format(
                '/'.join(aliases)
            ))

    def make_collection_service(self, previous_service, previous_namespaces, managed_class, level):
        """
        Called from create_collection as a recursive method to collect all
        submanagers of the root manager we want to manager with this service.
        """
        namespace = managed_class.get_name()
        namespaces = previous_namespaces + (namespace, )
        url = previous_service.resource_url.add_segment(namespace)

        config_key = '.'.join(namespaces)
        conf = self.configuration.get(config_key)

        service = CollectionService(
            previous_service,
            ServedManager(
                managed_class.manager_class,
                conf,
                url,
                namespaces,
                managed_class.extractor,
                lock=self.lock,
            ))

        self._collection_services[namespaces] = service

        # level to avoid max recursion.
        self.create_collection_service(
            managed_class.manager_class, namespaces, service, level + 1)

    def create_collection_service(self, collection, ns, previous_service, level):
        if level >= MAX_LEVEL:
            return

        for managed_class in collection.get_managed_classes():
            self.make_collection_service(previous_service, ns, managed_class, level)

    def setup_bottle(self, app):
        """
        Route the managers inside the given bottle app.
        """
        logger.debug('Setting %s', self.url)
        for service in self._collection_services.values():
            service.setup_bottle(app)
