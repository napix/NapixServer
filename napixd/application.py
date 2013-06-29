#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import bottle

from napixd.services import Service

logger = logging.getLogger('Napix.application')

class NapixdBottle(bottle.Bottle):
    """
    Napix bottle application.
    This bottle contains the automatic detection of services.
    """

    def __init__(self, loader):
        """
        Create a new bottle app.
        The services served by this bottle are either given in the services parameter or guessed
        with the config of the application

        The service parameter is a list of Service instances that will be served by this app.
        When the paramater is not given or is None, the list is generated with the default conf.

        """
        super(NapixdBottle,self).__init__(autojson=False)
        self.root_urls = set()
        self.loader = loader

        load =  self.loader.load()
        self.make_services( load.managers )

        self.setup_bottle()

    def make_services( self, managers):
        """
        Load the services with the managers found
        return a list of Services instances
        """
        for mi in managers:
            service = Service( mi.manager, mi.alias, mi.config )
            logger.debug('Creating service %s', service.url)
            #add new routes
            service.setup_bottle( self)
            self.root_urls.add( service.url )

    def reload(self):
        load = self.loader.load()
        logger.info('Reloading')

        #remove old routes
        for mi in load.old_managers:
            rule = '/' + mi.alias
            prefix = rule + '/'
            self.routes = [ r
                    for r in self.routes
                    if not r.rule.startswith(prefix) and r.rule != rule ]
            self.root_urls.discard( mi.alias )

        self.make_services( load.new_managers )

        #reset the router
        self.router = bottle.Router()
        for route in self.routes:
            self.router.add(route.rule, route.method, route, name=route.name)

        #add errord routes
        for me in load.error_managers:
            self.register_error( me)

    def register_error(self, me):
        self.route( '/%s'%me.alias, callback=self._error_service_factory( me.cause ))
        self.route( '/%s/'%me.alias, callback=self._error_service_factory( me.cause ))
        self.route( '/%s/<catch_all:path>'%me.alias, callback=self._error_service_factory( me.cause ))

        self.root_urls.add( me.alias )

    def setup_bottle(self):
        """
        Register the services into the app
        """
        #/ route, give the services
        self.route('/',callback=self.slash)

        #Error handling for not found and invalid
        self.error(404)(self._error_handler_factory(404))
        self.error(405)(self._error_handler_factory(405))
        self.error(400)(self._error_handler_factory(400))
        self.error(500)(self._error_handler_factory(500))


    def slash(self):
        """
        /  view; return the list of the first level services of the app.
        """
        return ['/'+x for x in self.root_urls ]

    def _error_handler_factory(self,code):
        """ 404 view """
        def inner(exception):
            bottle.response.status = code
            bottle.response['Content-Type'] = 'text/plain'
            return exception.body
        return inner

    def _error_service_factory( self, cause):
        def inner( catch_all ):
            raise cause
        return inner

