#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging

from napixd.services import Service

logger = logging.getLogger('Napix.application')


class NapixdBottle(object):
    """
    The Main Application class.
    This object is used to connect the :class:`napixd.services.Service`
    to the WSGI framework.

    *loader* is a :class:`napixd.loader.Loader` instance
    used to find :class:`napixd.manager.base.Manager` classes.
    """

    def __init__(self, loader, server):
        self._root_urls = []
        self.loader = loader

        self.server = server
        self.server.route('/', self.slash)

        load = self.loader.load()
        self.make_services(load.managers)

    def make_services(self, managers):
        """
        Make :class:`napixd.services.Service` instance from
        the :class:`napixd.loader.ManagerImport` given by the loader.
        """
        for mi in managers:
            service = Service(mi.manager, mi.alias, mi.config)
            logger.debug('Creating service %s', service.url)
            # add new routes
            service.setup_bottle(self.server)
            self._root_urls.append(service.url)

        self._root_urls.sort()

    def reload(self):
        """
        Launch a reloading sequence.

        It calls :meth:`napixd.loader.Loading.load` and
        manages the new and old managers and errors.
        """
        load = self.loader.load()
        logger.info('Reloading')

        # remove old routes
        if logger.isEnabledFor(logging.DEBUG) and load.old_managers:
            logger.debug('Old services: %s',
                         ', '.join(map(unicode, load.old_managers)))
        for mi in load.old_managers:
            rule = '/' + mi.alias
            self.server.unroute(rule, all=True)
            self._root_urls.remove(mi.alias)

        if logger.isEnabledFor(logging.DEBUG) and load.new_managers:
            logger.debug('New services: %s',
                         u', '.join(map(unicode, load.new_managers)))
        self.make_services(load.new_managers)

        if logger.isEnabledFor(logging.DEBUG) and load.error_managers:
            logger.debug('Error services: %s',
                         u', '.join(map(unicode, load.error_managers)))
        # add errord routes
        for me in load.error_managers:
            self.register_error(me)

    def register_error(self, me):
        """
        Set up the routes for a :class:`napixd.loader.ManagerError`.

        The routes will respond to any query by raising the
        :attr:`napixd.loader.ManagerError.cause` of the errors.
        """
        logger.debug('Setup routes for error, %s', me.alias)
        callback = self._error_service_factory(me.cause)
        self.server.route('/{0}'.format(me.alias), callback)
        self.server.route('/{0}/'.format(me.alias), callback, catchall=True)

        self._root_urls.append(me.alias)
        self._root_urls.sort()

    def slash(self, request):
        """
        /  view; return the list of the first level services of the app.
        """
        return ['/' + x for x in self._root_urls]

    def _error_service_factory(self, cause):
        def inner_error_service_factory(*catch_all, **more_catch_all):
            raise cause
        return inner_error_service_factory
