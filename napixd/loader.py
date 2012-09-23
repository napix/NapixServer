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

from napixd import HOME
from .conf import Conf
from .services import Service
from .managers import Manager
from .autodoc import Autodocument
from .thread_manager import thread_manager
from .notify import Notifier

import bottle
from .plugins import ConversationPlugin, ExceptionsCatcher, AAAPlugin, UserAgentDetector

class AllOptions(object):
    def __contains__(self, x):
        return True

def get_bottle_app( options =None ):
    """
    Return the bottle application for the napixd server.
    """
    options = options if options is not None else AllOptions()
    napixd = NapixdBottle( options=options)

    conf =  Conf.get_default('Napix.auth')
    if 'useragent' in options:
        napixd.install( UserAgentDetector() )
    if 'auth' in options:
        if conf :
            napixd.install(AAAPlugin( conf))
        else:
            logger.warning('No authentification configuration found.')

    #attach autoreloaders
    if 'reload' in options:
        napixd.launch_autoreloader()
    return napixd

class Loader( object):
    AUTO_DETECT_PATH = '/var/lib/napix/auto'

    def __init__( self):
        self.timestamp = 0
        self.paths = [
                self.AUTO_DETECT_PATH,
                os.path.join( HOME, 'auto')
                ]
        self._loading = None

    def load( self):
        self._loading = Loading( self.timestamp, self.paths, self._loading)
        self.timestamp = time.time()
        return self._loading

class Loading(object):
    def __init__( self, start, paths, previous = None):
        self.paths = paths
        self.timestamp = start
        self.errors = {}

        #every managers that we found
        self.managers = set( self.find_managers())
        for alias, manager in self.managers:
            self.setup( manager )

        #Every manager that we did not find
        if previous is not None:
            self.new_managers = self.managers - previous.managers
            self.old_managers = previous.managers - self.managers
        else:
            self.new_managers = self.managers
            self.old_managers = set()

        self.error_managers = list()
        if self.errors:
            for alias, manager in self.old_managers:
                if manager.__module__ in self.errors:
                    self.error_managers.append( ( alias, manager, self.errors[ manager.__module__ ] ))
            if previous and previous.error_managers:
                for alias, manager, cause in previous.error_managers:
                    if manager.__module__ in self.errors:
                        self.error_managers.append( ( alias, manager, self.errors[ manager.__module__ ] ))

    def setup( self, manager):
        if manager.direct_plug() is None:
            managed_classes = []
        else:
            managed_classes = [ self._setup( manager, submanager)
                    for submanager in manager.get_managed_classes() ]
        managed_classes = filter( bool, managed_classes)
        manager.set_managed_classes(managed_classes)

    def _setup(self, manager, manager_ref):
        if isinstance( manager_ref, type):
            self.setup( manager_ref )
            return manager_ref
        elif isinstance( manager_ref, basestring):
            if '.' in manager_ref:
                module, dot, manager_name = manager_ref.rpartition('.')
                try:
                    self._import(module)
                    submanager = getattr( sys.modules[ module ], manager_name)
                except ImportError:
                    logger.error( 'Fail to load the managed class %s of %s from %s',
                            manager_name, manager.get_name(), module )
                    return
                except AttributeError:
                    logger.error( 'No managed class %s of %s inside %s',
                            manager_name, manager.get_name(), module )
                    return
            else:
                try:
                    submanager = getattr( sys.modules[ manager.__module__ ], manager_ref)
                except AttributeError:
                    logger.error( 'Fail to load the managed class %s of %s from same module',
                            manager_ref, manager.get_name() )
                    return
            self.setup( submanager )
            return submanager
        else:
            logger.error( 'managed_class of %s (%s.%s) should be a string, a Manager subclass or a list of these',
                    manager.get_name(), manager.__module__, manager.__name__)
            return manager_ref

    def __iter__(self):
        return iter( self.managers )

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
                self.errors[ module_path ] = e
                continue
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
                self.errors[ module_name ] = e
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

    def __init__(self, services=None, no_conversation=False, options=None):
        """
        Create a new bottle app.
        The services served by this bottle are either given in the services parameter or guessed
        with the config of the application

        The service parameter is a list of Service instances that will be served by this app.
        When the paramater is not given or is None, the list is generated with the default conf.

        the no_conversation parameter may be set to True to disable the ConversationPlugin.
        """
        self.options = options if options is not None else AllOptions()
        super(NapixdBottle,self).__init__(autojson=False)
        self._start()
        self.root_urls = set()

        self.loader = None
        if services is None:
            self.loader = self.loader_class()
            load =  self.loader.load()
            services = self.make_services( load.managers )
            if 'doc' in self.options:
                doc = Autodocument()
                thread_manager.do_async( doc.generate_doc, fn_args=(load.managers,),
                        give_thread=False, on_success=self.doc_set_root)
        else:
            self.root_urls.update( s.url for s in services )
            for service in services:
                service.setup_bottle( self)

        if not no_conversation :
            self.install(ConversationPlugin())
        self.install(ExceptionsCatcher())
        self.notify_thread = False

        self.on_stop = []
        self.setup_bottle()

        if 'notify' in self.options and Conf.get_default('Napix.notify.url'):
            notifier = Notifier( self)
            self.on_stop.append( notifier.stop)
            notifier.start()

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
        for alias, manager in managers:
            config = Conf.get_default().get( alias )
            service = Service( manager, alias, config )
            logger.debug('Creating service %s', service.url)
            yield service

    def _start( self):
        Conf.make_default()
        bottle.DEBUG = Conf.get_default('Napix.debug')
        #self.services = list(self.loader)

    def _reload(self):
        console = logging.getLogger( 'Napix.console')
        if self.loader is None:
            return
        self._start()
        load = self.loader.load()
        console.info( 'Reloading')

        #remove old routes
        for alias,manager in load.old_managers:
            prefix = '/' + alias
            self.routes = [ r for r in self.routes if not r.rule.startswith(prefix) ]
            self.root_urls.discard( alias )

        self.make_services( load.new_managers )

        #reset the router
        self.router = bottle.Router()
        for route in self.routes:
            self.router.add(route.rule, route.method, route, name=route.name)

        #add errord routes
        for alias, manager, cause in load.error_managers:
            self.route( '/%s<catch_all:path>'%alias,
                    callback=self._error_service_factory( cause ))
            self.root_urls.add( alias )

    def setup_bottle(self):
        """
        Register the services into the app
        """
        #/ route, give the services
        self.route('/',callback=self.slash)
        if 'reload' in self.options:
            self.route('/_napix_reload',callback=self.reload)

        #Error handling for not found and invalid
        self.error(404)(self._error_handler_factory(404))
        self.error(400)(self._error_handler_factory(400))
        self.error(500)(self._error_handler_factory(500))

        if 'webclient' in self.options:
            webclient_path = self.get_webclient_path()
            if webclient_path:
                logger.info( 'Using %s as webclient', webclient_path)
                self.route('/_napix_js<filename:path>',
                        callback=self.static_factory( webclient_path),
                        skip = [ 'authentication_plugin', 'conversation_plugin', 'user_agent_detector' ] )

    def get_webclient_path(self):
        for directory in [ Conf.get_default('Napix.webclient.path'),
                os.path.join( HOME, 'web'),
                os.path.join( os.path.dirname( __file__), 'web')
                ]:
            logger.debug( 'Try WebClient in directory %s', directory)
            if directory and os.path.isdir( directory):
                return directory

    def launch_autoreloader(self):
        signal.signal( signal.SIGHUP, self.on_sighup)

        if ( self.loader is not None and has_inotify and
                Conf.get_default('Napix.loader.autoreload')):
            logger.info( 'Launch Napix autoreloader')
            watch_manager = pyinotify.WatchManager()
            for path in self.loader.paths:
                if os.path.isdir( path):
                    watch_manager.add_watch( path, pyinotify.IN_CLOSE_WRITE)

            self.notify_thread = pyinotify.ThreadedNotifier( watch_manager, self.on_file_change)
            self.notify_thread.start()
            self.on_stop.append( self.notify_thread.stop )
        elif not has_inotify:
            logger.info('Did not find pyinotify, reload on file change support disabled')

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

    def static_factory(self, root):
        def static( filename = 'index.html' ):
            if filename.endswith('/'):
                filename += 'index.html'
            return bottle.static_file( filename, root =  root )
        return static

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
            return exception.output
        return inner

    def _error_service_factory( self, cause):
        def inner( catch_all ):
            raise cause
        return inner

