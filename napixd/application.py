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

    def __init__(self, services=None, loader=None):
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
        if services is None:
            load =  self.loader.load()
            services = self.make_services( load.managers )
        else:
            self.root_urls.update( s.url for s in services )
            for service in services:
                service.setup_bottle( self)

        self.on_stop = []
        self.setup_bottle()

    def doc_set_root(self, root):
        self.route('/_napix_autodoc<filename:path>',
                callback= self.static_factory(root ),
                skip = [ 'authentication_plugin', 'conversation_plugin', 'user_agent_detector' ] )

    def make_services( self, managers):
        for service in self._make_services( managers ):
            #add new routes
            service.setup_bottle( self)
            self.root_urls.add( service.url )

    def _make_services( self, managers ):
        """
        Load the services with the managers found
        return a list of Services instances
        """
        for manager, alias, config in managers:
            service = Service( manager, alias, config )
            logger.debug('Creating service %s', service.url)
            yield service

    def reload(self):
        console = logging.getLogger( 'Napix.console')
        if self.loader is None:
            return
        load = self.loader.load()
        console.info( 'Reloading')

        #remove old routes
        for manager, alias, config in load.old_managers:
            prefix = '/' + alias
            self.routes = [ r for r in self.routes if not r.rule.startswith(prefix) ]
            self.root_urls.discard( alias )

        self.make_services( load.new_managers )

        #reset the router
        self.router = bottle.Router()
        for route in self.routes:
            self.router.add(route.rule, route.method, route, name=route.name)

        #add errord routes
        for manager, alias, cause in load.error_managers:
            self.route( '/%s<catch_all:path>'%alias,
                    callback=self._error_service_factory( cause ))
            self.root_urls.add( alias )

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

    def stop(self):
        for stop in self.on_stop:
            stop()

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

