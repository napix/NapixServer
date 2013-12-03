#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The service class is the interface between the managers and the web server

The service plug itself in the url router of Bottle, and will instantiate the
appropriate Napix Manager to handle the request.
"""

import logging

from napixd.services.collection import (
    FirstCollectionService,
    CollectionService
)
from napixd.services.lock import LockFactory, ConnectionFactory

__all__ = [
    'Service',
]

logger = logging.getLogger('Napix.service')

MAX_LEVEL = 5
lock_factory = LockFactory(ConnectionFactory())


class ServedManager(object):
    def __init__(self, manager_class, config, g 


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
        self.collection_services = []
        self.url = namespace
        lock_conf = 'Lock' in configuration

        if lock_conf:
            self.lock = lock_factory(lock_conf)
        else:
            self.lock = None

        service = FirstCollectionService(
            collection, self.configuration, self.url, self.lock)
        self._append_service(service)
        self.create_collection_service(collection, service, 0)

    def _append_service(self, service):
        self.collection_services.append(service)

    def make_collection_service(self, previous_service, managed_class, level):
        """
        Called from create_collection as a recursive method to collect all
        submanagers of the root manager we want to manager with this service.
        """
        namespace = managed_class.get_name()
        config_key = '{0}.{1}'.format(previous_service.get_name(), namespace)
        service = CollectionService(
            previous_service,
            managed_class,
            self.configuration.get(config_key),
            namespace,
            self.lock,
        )
        self._append_service(service)
        # level to avoid max recursion.
        self.create_collection_service(
            managed_class.manager_class, service, level + 1)

    def create_collection_service(self, collection, previous_service, level):
        if level < MAX_LEVEL:
            for managed_class in collection.get_managed_classes():
                self.make_collection_service(previous_service, managed_class, level)

    def setup_bottle(self, app):
        """
        Route the managers inside the given bottle app.
        """
        logger.debug('Setting %s', self.url)
        for service in self.collection_services:
            app
            service.setup_bottle(app)
