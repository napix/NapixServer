#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger('Napix.loader')

import sys
import os.path
from .conf import Conf
from .services import Service
from .managers import Manager

import bottle
from .plugins import ConversationPlugin, ExceptionsCatcher, AAAPlugin

bottle.DEBUG = True
AUTO_DETECT_PATH = '/var/lib/napix/auto'

def get_bottle_app():
    """
    Return the bottle application for the napixd server.
    """
    napixd = NapixdBottle()
    napixd.setup_bottle()
    conf =  Conf.get_default().get('Napix.auth')
    if conf :
        napixd.install(AAAPlugin( conf))
    else:
        logger.warning('No authentification configuration found.')
    return napixd


class NapixdBottle(bottle.Bottle):
    """
    Napix bottle application.
    This bottle contains the automatic detection of services.
    """
    def __init__(self, services=None, no_conversation=False):
        """
        Create a new bottle app.
        The services served by this bottle are either given in the services parameter or guessed
        with the config of the application

        The service parameter is a list of Service instances that will be served by this app.
        When the paramater is not given or is None, the list is generated with the default conf.

        the no_conversation parameter may be set to True to disable the ConversationPlugin.
        """
        super(NapixdBottle,self).__init__(autojson=False)
        self.services = services or list(self._load_services())
        if not no_conversation :
            self.install(ConversationPlugin())
        self.install(ExceptionsCatcher())

    def setup_bottle(self):
        """
        Register the services into the app
        """
        for service in self.services:
            service.setup_bottle(self)
        #/ route, give the services
        self.route('/',callback=self.slash)
        self.route('/_napix_js/', callback= self.static,
                skip = [ 'authentication_plugin', 'conversation_plugin' ] )
        self.route('/_napix_js/<filename:path>', callback= self.static,
                skip = [ 'authentication_plugin', 'conversation_plugin' ] )
        #Error handling for not found and invalid
        self.error(404)(self._error_handler_factory(404))
        self.error(400)(self._error_handler_factory(400))
        self.error(500)(self._error_handler_factory(500))

    def static(self, filename = 'index.html' ):
        return bottle.static_file( filename, root = os.path.join( os.path.dirname( __file__),'web'))

    def _load_managers( self):
        for manager in self._load_conf_managers():
            yield manager
        for manager in self._load_auto_detect():
            yield manager

    def _load_conf_managers(self):
        """
        Load the managers with the conf
        return a list of Manager subclasses
        """
        managers_conf = Conf.get_default().get('Napix.managers')
        for alias, manager_path in managers_conf.items():
            module_path, x, manager_name = manager_path.rpartition('.')
            module = self._import( module_path )
            logger.debug('load %s',manager_name)
            manager = getattr( module, manager_name)
            yield alias, manager

    def _import( self, module_path ):
        logger.debug('import %s', module_path)
        __import__(module_path)
        return sys.modules[module_path]

    def _load_auto_detect( self ):
        sys.path.app( AUTO_DETECT_PATH )
        for filename in os.path.listdir( AUTO_DETECT_PATH ):
            if filename.startswith('.'):
                continue
            module_name, dot, py = filename.rpartition('.')
            if not dot or py != 'py':
                continue
            module = self._import(module_name)
            content = getattr( module, '__all__') or dir( module_name )
            for attr in content:
                obj = getattr(module_name, attr)
                if isinstance( obj, type) and issubclass( obj, Manager):
                    yield obj.get_name(), obj


    def _load_services(self):
        """
        Load the services with the managers found
        return a list of Services instances
        """
        for alias, manager in self._load_managers():
            config = Conf.get_default().get( alias )
            service = Service( manager, config )
            logger.debug('service %s', service.url)
            yield service

    def slash(self):
        """
        /  view; return the list of the first level services of the app.
        """
        return ['/'+x.url for x in self.services ]

    def _error_handler_factory(self,code):
        """ 404 view """
        def inner(exception):
            bottle.response.status = code
            bottle.response['Content-Type'] = 'text/plain'
            return exception.output
        return inner
