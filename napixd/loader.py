#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger('Napix.loader')

import sys
import time
import os
import signal

try:
    import pyinotify
    has_inotify = True
except ImportError:
    has_inotify = False

from .conf import Conf
from .services import Service
from .managers import Manager

import bottle
from .plugins import ConversationPlugin, ExceptionsCatcher, AAAPlugin, UserAgentDetector

def get_bottle_app():
    """
    Return the bottle application for the napixd server.
    """
    napixd = NapixdBottle()
    napixd.setup_bottle()

    conf =  Conf.get_default('Napix.auth')
    napixd.install( UserAgentDetector() )
    if conf :
        napixd.install(AAAPlugin( conf))
    else:
        logger.warning('No authentification configuration found.')

    #attach autoreloaders
    napixd.launch_autoreloader()
    return napixd

class Loader( object):
    AUTO_DETECT_PATH = '/var/lib/napix/auto'

    def __init__( self):
        self.timestamp = 0
        self.paths = [
                self.AUTO_DETECT_PATH,
                os.path.join( os.path.dirname( __file__ ), '..', 'auto')
                ]

    def __iter__(self):
        logger.debug('Start loading since %s', self.timestamp)
        return self.find_services()

    def find_services(self):
        """
        Load the services with the managers found
        return a list of Services instances
        """
        for alias, manager in self.find_managers():
            config = Conf.get_default().get( alias )
            if alias and not config.get('url'):
                config['url'] = alias
            service = Service( manager, config )
            logger.debug('Creating service %s', service.url)
            yield service
        #reset the timestamp
        self.timestamp = time.time()

    def find_managers( self):
        for manager in self.find_managers_from_conf():
            yield manager
        for manager in self.find_managers_auto():
            yield manager

    def find_managers_from_conf(self):
        """
        Load the managers with the conf
        return a list of Manager subclasses
        """
        managers_conf = Conf.get_default().get('Napix.managers')
        for alias, manager_path in managers_conf.items():
            module_path, x, manager_name = manager_path.rpartition('.')
            try:
                module = self._import( module_path )
            except ImportError as e:
                logger.error( 'Failed to import %s from conf: %s', module_path, str(e))
                raise
            logger.debug('load %s from conf', manager_path)
            manager = getattr( module, manager_name)
            yield alias, manager

    def find_managers_auto( self):
        for path in self.paths :
            if os.path.isdir( path):
                for x in self._load_auto_detect(path):
                    yield x

    def _load_auto_detect( self, path ):
        logger.debug( 'inspecting %s', path)
        if not path in sys.path:
            sys.path.append(path)
        for filename in os.listdir(path):
            if filename.startswith('.'):
                continue
            module_name, dot, py = filename.rpartition('.')
            if not dot or py != 'py':
                continue
            try:
                module = self._import(module_name)
            except ImportError as e:
                logger.error( 'Failed to import %s from autoload: %s', module_name, str(e))
                continue

            content = getattr( module, '__all__', False) or dir( module)
            for attr in content:
                obj = getattr(module, attr)
                if isinstance( obj, type) and issubclass( obj, Manager):
                    if obj.detect():
                        yield obj.get_name(), obj

    def _import( self, module_path ):
        if not module_path in sys.modules:
            #first module import
            logger.debug('import %s', module_path)
            try:
                __import__(module_path)
            except ImportError:
                raise
            except Exception as e:
                raise ImportError, repr(e)
            return sys.modules[module_path]

        module = sys.modules[module_path]
        try:
            if module.__file__.endswith('pyc'):
                module_file = module.__file__[:-1]
            else:
                module_file = module.__file__

            last_modif = os.stat(module_file).st_mtime
            logger.debug( 'Module %s last modified at %s', module_path, last_modif)
        except OSError:
            raise ImportError, 'Module does not exists anymore'

        if last_modif > self.timestamp:
            #modified since last access
            logger.debug( 'Reloading module %s', module_path)
            try:
                reload( module)
            except ImportError as e:
                raise
            except Exception as e:
                raise ImportError, repr(e)
        return module


class NapixdBottle(bottle.Bottle):
    """
    Napix bottle application.
    This bottle contains the automatic detection of services.
    """
    loader_class = Loader

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
        self.loader = services or self.loader_class()
        self._start()
        if not no_conversation :
            self.install(ConversationPlugin())
        self.install(ExceptionsCatcher())
        self.notify_thread = False

        self.on_stop = []

    def launch_autoreloader(self):
        signal.signal( signal.SIGHUP, self.on_sighup)

        if has_inotify and Conf.get_default('Napix.loader.autoreload'):
            logger.info( 'Launch Napix autoreloader')
            watch_manager = pyinotify.WatchManager()
            for path in self.loader.paths:
                watch_manager.add_watch( path, pyinotify.IN_CLOSE_WRITE)

            self.notify_thread = pyinotify.ThreadedNotifier( watch_manager, self.on_file_change)
            self.notify_thread.start()
            self.on_stop.append( self.notify_thread.stop )

    def _start( self):
        Conf.make_default()
        bottle.DEBUG = Conf.get_default('Napix.debug')
        self.services = list(self.loader)

    def _setup_bottle_services(self):
        for service in self.services:
            service.setup_bottle(self)

    def setup_bottle(self):
        """
        Register the services into the app
        """
        self._setup_bottle_services()
        #/ route, give the services
        self.route('/',callback=self.slash)
        self.route('/_napix_reload',callback=self.reload)
        self.route('/_napix_js/', callback= self.static,
                skip = [ 'authentication_plugin', 'conversation_plugin', 'user_agent_detector' ] )
        self.route('/_napix_js/<filename:path>', callback= self.static,
                skip = [ 'authentication_plugin', 'conversation_plugin', 'user_agent_detector' ] )
        #Error handling for not found and invalid
        self.error(404)(self._error_handler_factory(404))
        self.error(400)(self._error_handler_factory(400))
        self.error(500)(self._error_handler_factory(500))

    def on_sighup(self, signum, frame):
        logger.info('Caught SIGHUP, reloading')
        self._reload()

    def on_file_change( self, event):
        if ( event.dir or not event.name.endswith('.py')):
            return
        logger.info('Caught file change, reloading')
        self._reload()

    def reload( self):
        if not Conf.get_default().get('Napix.debug'):
            raise bottle.HTTPError( 403, 'Not in debug mode, HTTP reloading is not possible')
        logger.info('Asked to do so, reloading')
        self._reload()

    def _reload(self):
        self._start()
        self._setup_bottle_services()

    def static(self, filename = 'index.html' ):
        if filename.endswith('/'):
            filename += 'index.html'
        return bottle.static_file( filename, root = os.path.join( os.path.dirname( __file__),'web'))

    def slash(self):
        """
        /  view; return the list of the first level services of the app.
        """
        return ['/'+x.url for x in self.services ]

    def stop(self):
        for stop in self.on_stop:
            stop()

    def _error_handler_factory(self,code):
        """ 404 view """
        def inner(exception):
            bottle.response.status = code
            bottle.response['Content-Type'] = 'text/plain'
            return exception.output
        return inner

