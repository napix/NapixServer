#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import bottle

from napixd.services import Service

logger = logging.getLogger('Napix.application')


class NapixdBottle(bottle.Bottle):
    """
    The Bottle Application class.
    This object is used to connect the :class:`napixd.services.Service`
    to the Bottle framework.

    *loader* is a :class:`napixd.loader.Loader` instance
    used to find :class:`napixd.manager.base.Manager` classes.
    """

    def __init__(self, loader):
        super(NapixdBottle, self).__init__(autojson=False)
        self.root_urls = set()
        self.loader = loader

        load = self.loader.load()
        self.make_services(load.managers)

        self.setup_bottle()

    def make_services(self, managers):
        """
        Make :class:`napixd.services.Service` instance from
        the :class:`napixd.loader.ManagerImport` given by the loader.
        """
        for mi in managers:
            service = Service(mi.manager, mi.alias, mi.config)
            logger.debug('Creating service %s', service.url)
            # add new routes
            service.setup_bottle(self)
            self.root_urls.add(service.url)

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
            prefix = rule + '/'
            self.routes = [r for r in self.routes
                           if not r.rule.startswith(prefix) and r.rule != rule]
            self.root_urls.discard(mi.alias)

        if logger.isEnabledFor(logging.DEBUG) and load.new_managers:
            logger.debug('New services: %s',
                         u', '.join(map(unicode, load.new_managers)))
        self.make_services(load.new_managers)

        # reset the router
        self.router = bottle.Router()
        for route in self.routes:
            self.router.add(route.rule, route.method, route, name=route.name)

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
        self.route('/{0}'.format(me.alias),
                   callback=self._error_service_factory(me.cause))
        self.route('/{0}/'.format(me.alias),
                   callback=self._error_service_factory(me.cause))
        self.route('/{0}/<catch_all:path>'.format(me.alias),
                   callback=self._error_service_factory(me.cause))

        self.root_urls.add(me.alias)

    def setup_bottle(self):
        """
        Register the services into the app
        """
        #/ route, give the services
        self.route('/', callback=self.slash)

        # Error handling for not found and invalid
        self.error(404)(self._error_handler_factory(404))
        self.error(405)(self._error_handler_factory(405))
        self.error(400)(self._error_handler_factory(400))
        self.error(500)(self._error_handler_factory(500))
        self.error(429)(self._error_handler_factory(429))

    def slash(self):
        """
        /  view; return the list of the first level services of the app.
        """
        return ['/' + x for x in self.root_urls]

    def _error_handler_factory(self, code):
        """ 404 view """
        def inner_error_handler(exception):
            bottle.response.status = code
            bottle.response['Content-Type'] = 'text/plain'
            return exception.body
        return inner_error_handler

    def _error_service_factory(self, cause):
        def inner_error_service_factory(*catch_all, **more_catch_all):
            raise cause
        return inner_error_service_factory
