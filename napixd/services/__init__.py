#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The service class is the interface between the managers and the web server

The service plug itself in the url router of Bottle, and will instantiate the
appropriate Napix Manager to handle the request.
"""

import sys
import logging

from napixd.services.urls import URL
from napixd.services.collection import (
    FirstCollectionService,
    CollectionService
)
from napixd.services.requests import (
    ServiceCollectionRequest,
    ServiceResourceRequest,
)
from napixd.services.lock import LockFactory


logger = logging.getLogger('Napix.service')

MAX_LEVEL = 5
lock_factory = LockFactory()


class ServedManager(object):
    """
    Intermediary object the objects needed to serve a a :class:`napixd.manager.base.Manager` class.

    It includes *configuration*, a :class:`napixd.conf.BaseConf` instance
    used to configure the instances, an :class:`napixd.service.urls.URL` at wich the manager
    is served.

    The *extractor* is the extractor used for the managed classes.
    """
    def __init__(self, manager_class, configuration, url, lock=None, extractor=None):
        self.manager_class = manager_class
        self.url = url
        self.configuration = configuration
        self.lock = lock
        self.extractor = extractor

    def __eq__(self, other):
        return (isinstance(other, ServedManager) and
                self.manager_class == other.manager_class and
                self.url == other.url and
                self.configuration == other.configuration and
                self.extractor == other.extractor and
                self.lock == other.lock
                )

    @property
    def resource_fields(self):
        """
        The resource fields of the manager as a dict.
        """
        rf = self.manager_class._resource_fields
        return dict((key, dict(value)) for key, value in rf.items())

    @property
    def source(self):
        """
        The location of the code of the server manager class.
        """
        mc = self.manager_class
        return {
            'class': mc.__name__,
            'module': mc.__module__,
            'file': sys.modules[mc.__module__].__file__,
        }

    @property
    def meta_data(self):
        """
        All the meta datas of the manager.
        """
        mc = self.manager_class
        return {
            'doc': (mc.__doc__ or '').strip(),
            'direct_plug': False if mc.get_managed_classes() else None,
            'views': dict((format_, (cb.__doc__ or '').strip())
                          for (format_, cb)
                          in mc.get_all_formats().items()),
            'managed_class': [m.get_name() for m in mc.get_managed_classes()],
            'actions': dict((action, getattr(mc, action).__doc__)
                            for action in mc.get_all_actions()),
            'collection_methods': ServiceCollectionRequest.available_methods(mc),
            'resource_methods': ServiceResourceRequest.available_methods(mc),
            'resource_fields': self.resource_fields,
            'source': self.source,
        }

    def get_all_actions(self):
        """
        Returns a collection of :class:`ServedAction` for the actions
        of the served manager.
        """
        return [ServedAction(self, action)
                for action in self.manager_class.get_all_actions()]


class ServedAction(object):
    """
    An intermediary object for an action of a :class:`ServedManager`.
    """
    def __init__(self, served_manager, action_name):
        self.name = action_name
        self.lock = served_manager.lock
        self.action = getattr(served_manager.manager_class, action_name)
        self.doc = (self.action.__doc__ or '').strip()
        self.source = served_manager.source
        self.source['method'] = self.action.__name__

    @property
    def resource_fields(self):
        rf = self.action.resource_fields
        return dict((key, dict(value)) for key, value in rf.items())

    @property
    def meta_data(self):
        return {
            'resource_fields': self.resource_fields,
            'doc': self.doc,
            'mandatory': self.action.mandatory,
            'optional': self.action.optional,
            'source': self.source,
        }


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
        self.url = URL([namespace])

        if 'Lock' in configuration:
            lock_conf = configuration.get('Lock')
            if not 'name' in lock_conf:
                raise ValueError('Lock configuration must have at least a name')

            logger.info('Creating lock %s for %s', lock_conf.get('name'), namespace)
            self.lock = lock_factory(lock_conf)
        else:
            self.lock = None

        service = FirstCollectionService(
            ServedManager(
                collection,
                self.configuration,
                self.url,
                lock=self.lock,
            ))
        self._append_service(service)
        self.create_collection_service(collection, namespace, service, 0)

    def _append_service(self, service):
        self.collection_services.append(service)

    def make_collection_service(self, previous_service, previous_ns, managed_class, level):
        """
        Called from create_collection as a recursive method to collect all
        submanagers of the root manager we want to manager with this service.
        """
        namespace = managed_class.get_name()
        url = previous_service.resource_url.add_segment(namespace)

        config_key = '{0}.{1}'.format(previous_ns, namespace)
        conf = self.configuration.get(config_key)

        service = CollectionService(
            previous_service,
            ServedManager(
                managed_class.manager_class,
                conf,
                url,
                lock=self.lock,
                extractor=managed_class.extractor
            ))
        self._append_service(service)
        # level to avoid max recursion.
        self.create_collection_service(
            managed_class.manager_class, config_key, service, level + 1)

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
        for service in self.collection_services:
            service.setup_bottle(app)
