#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The launcher defines the infrastructure to prepare and run the Napix Server.

:class:`Setup` is intended to be overidden to customize running
as an integrated component or in a specialized server.
"""

import logging
import logging.handlers
import os
import sys
import optparse

from napixd import get_file, get_path
from napixd.utils.tracingset import TracingSet

from napixd.conf import Conf, ConfLoader


__all__ = ['launch', 'Setup']

logger = logging.getLogger('Napix.Server')
console = logging.getLogger('Napix.console')


def launch(options, setup_class=None):
    """
    Helper function to run Napix.

    It creates a **setup_class** (by default :class:`Setup` instance with the given **options**.

    **options** is an iterable.

    The exceptions are caught and logged.
    The function will block until the server is killed.
    """
    setup_class = setup_class or Setup
    sys.stdin.close()
    try:
        setup = setup_class(options)
    except CannotLaunch as e:
        logger.critical(e)
        return
    except Exception as e:
        logger.exception(e)
        logger.critical(e)
        return

    try:
        setup.run()
    except (KeyboardInterrupt, SystemExit):
        return
    except Exception, e:
        if 'print_exc' in setup.options:
            logger.exception(e)
        logger.critical(e)


class CannotLaunch(Exception):
    """
    Exception raised when the server encounters a fatal error
    preventing it from running.
    """
    pass


class Setup(object):
    """
    The class that prepares and run a Napix server instance.

    It takes its **options** as argument.
    It is an iterable of strings.

    .. attribute:: DEFAULT_OPTIONS

        A set of options to use by default.

    .. attribute:: LOG_FILE

        A path to a log file.

    .. attribute:: HELP_TEXT

        The help provided to the user if the option help is used.

    .. attribute:: service_name

        The name of this daemon.
        It is used (amongst others) by the auth plugin
        for the requests to the central.
    """
    DEFAULT_HOST = '0.0.0.0'
    DEFAULT_PORT = 8002
    DEFAULT_OPTIONS = set([
        'app',  # Launch the application
        # 'notify', # the thread of periodic notifications
        'useragent',  # the html page shown when a browser access directly
        'auth',  # the auth interface
        'reload',  # the reloader on signal page and automatic
        'webclient',  # the web client,
        'gevent',  # Use gevent
        'cors',  # Set CORS headers
        'auto',
        'conf',
        'time',  # Show duration
        'logger',  # Ouput of the logs in the console is consistent
        'docs',
        'dotconf',
        'central',  # Use a central Napix server for the authentication
    ])

    LOG_FILE = get_file('log/napix.log')
    HELP_TEXT = '''
napixd daemon runner.
usage: napixd [--port PORT] [only] [(no)option ...]
       napixd help: show this message

option to enable the option.
nooption to disable the option

napixd help will show this message
napixd only ... will run only the given options and not enable the defaults options
napixd options ... will show the options enabled in this configuration.
    It takes into account 'only', 'no<option>', and the defaults.

options are:
Default options:
    app:        Launch the application
    useragent:  The html page shown when a browser access directly
    auth:       The authentication component
    reload:     The reloader events attachement on signal, page and inotify
    webclient:  The web interface accessible on /_napix_js/
    gevent:     Use gevent as the wsgi interface
    auto:       Load from HOME/auto/ directory
    conf:       Load from the Napix.managers section of the config
    time:       Add custom header to show the duration of the request
    logger:     Standardize the ouptut on the console accross servers
    docs:       Generate automated documentation
    dotconf:    Use a dotconf file as the source of configuration
    central:    Use a central Napix server for the authentication

Non-default:
    uwsgi:      Use with uwsgi (by default when loading napixd.application)
    notify:     Enable the notification thread
    silent:     Do not show the messages in the console
    verbose:    Augment the ouptut of the loggers
    print_exc:  Show the exceptions in the console output
    times:      Add custom header to show the running time and the total time (requires gevent)
    pprint:     Enable pretty printing of output
    cors:       Add Cross-Origin Request Service headers
    secure:     Disable the request token signing
    localhost:  Listen on the loopback interface only
    autonomous-auth:    Use a local source of authentication
    hosts:      Check the HTTP Host header
    jwt:        Enables authentication by JSON Web Tokens

Meta-options:
    only:       Disable default options
    help:       Show this message and quit
    options:    Show the enabled options and quit
'''

    def __init__(self, options):
        parser = optparse.OptionParser(usage=self.HELP_TEXT)
        parser.add_option('-p', '--port',
                          help='The TCP port to listen to',
                          type='int',
                          default=self.DEFAULT_PORT)
        self.keys, options = parser.parse_args()

        nooptions = [opt[2:] for opt in options if opt.startswith('no')]

        options = set(options)
        if 'only' not in options:
            options = options.union(self.DEFAULT_OPTIONS)
        self.options = options = TracingSet(options.difference(nooptions))

        self.set_loggers()

        self.conf = self.get_conf()

        self.service_name = self.get_service_name()
        self.hosts = self.get_hostnames()

        console.info('Napixd Home is %s', get_path())
        console.info('Options are %s', ','.join(self.options))
        console.info('Starting process %s', os.getpid())
        console.info('Logging activity in %s', self.LOG_FILE)
        console.info('Service Name is %s', self.service_name)

    def get_conf(self):
        logger.info('Loading configuration')
        paths = [
            get_path('conf/'),
        ]
        if 'dotconf' in self.options:
            try:
                from napixd.conf.dotconf import ConfFactory
            except ImportError:
                raise CannotLaunch('dotconf option requires the external library dotconf')
            loader = ConfLoader(paths, ConfFactory())
            conf = loader()
        else:
            from napixd.conf.json import ConfFactory, CompatConf
            loader = ConfLoader(paths, ConfFactory())
            conf = CompatConf(loader())

        return Conf.set_default(conf)

    def _patch_gevent(self):
        if 'gevent' in self.options:
            try:
                import gevent
            except ImportError:
                raise CannotLaunch(
                    u'Cannot import gevent lib. Try to install it, or run napix with *nogevent* option')

            if gevent.version_info < (1, 0):
                raise CannotLaunch(
                    u'Napix require gevent >= 1.0, Try to install it, or run napix with *nogevent* option')

            from gevent.monkey import patch_all
            logger.info('Installing gevent monkey patch')
            patch_all()

    def run(self):
        """
        Run the Napix Server
        """

        if 'help' in self.options:
            print self.HELP_TEXT
            return 1
        if 'options' in self.options:
            print 'Enabled options are: ' + ' '.join(self.options)
            return

        self._patch_gevent()
        app = self.get_app()

        logger.info('Starting')
        try:
            if 'app' in self.options:
                server_options = self.get_server_options()
                application = self.apply_middleware(app)

                logger.info('Listening on %s:%s',
                            server_options['host'], server_options['port'])

                adapter_class = server_options.pop('server', None)
                if not adapter_class:
                    raise CannotLaunch('No server available')

                adapter = adapter_class(server_options)

                if self.options.unchecked:
                    console.warning('Unchecked Options are: %s',
                                    ','.join(self.options.unchecked))
                adapter.run(application)
        finally:
            console.info('Stopping')

        console.info('Stopped')

    def get_service_name(self):
        """
        Returns the name of the service.

        This name is cache in :attr:`service_name`

        The configuration option ``Napix.auth.service`` is used.
        If it does not exists, the name is fetched from :file:`/etc/hostname`
        """
        try:
            service = self.conf.get('service', type=unicode)
        except TypeError:
            try:
                service = self.conf.get('auth.service', type=unicode)
            except TypeError:
                raise CannotLaunch('The service name is not specified')

        if not service:
            logger.info(
                'No setting Napix.auth.service, guessing from /etc/hostname')
            try:
                with open('/etc/hostname', 'r') as handle:
                    return handle.read().strip()
            except IOError:
                logger.error('Cannot read hostname')
                return ''
        return service

    def get_auth_handler(self):
        """
        Load the authentication handler.
        """
        conf = self.conf.get('auth')
        from napixd.auth.plugin import AAAPlugin
        sources = self.get_auth_sources(conf)
        providers = self.get_auth_providers(conf)
        plugin = AAAPlugin(sources, providers, timed='time' in self.options)
        return plugin

    def get_auth_providers(self, conf):
        from napixd.auth.request import RequestParamaterChecker, HostChecker
        providers = [RequestParamaterChecker()]

        if 'hosts' in self.options:
            providers.append(HostChecker(self.hosts))

        if 'autonomous-auth' in self.options:
            from napixd.auth.autonomous import AutonomousAuthProvider
            providers.append(AutonomousAuthProvider.from_settings(conf))
            logger.info('Enable autonomous authentication')

        if 'central' in self.options:
            try:
                from napixd.auth.central import CentralAuthProvider
            except ImportError:
                raise CannotLaunch('Central authentication requires permissions')
            providers.append(CentralAuthProvider.from_settings(self.service_name, conf))
            logger.info('Enable central server authentication')

        return providers

    def get_auth_sources(self, conf):
        from napixd.auth.sources import (
            SecureAuthProtocol,
            NonSecureAuthProtocol,
        )
        sources = [SecureAuthProtocol()]
        if not 'secure' in self.options:
            sources.append(NonSecureAuthProtocol.from_settings(conf))
            logger.info('Enable authentication by tokens')
        if 'jwt' in self.options:
            from napixd.auth.jwt import JSONWebToken
            sources.append(JSONWebToken())
        return sources

    def get_napixd(self, server):
        """
        Return the main application for the napixd server.
        """
        from napixd.application import NapixdBottle
        from napixd.loader import Loader
        self.loader = loader = Loader(self.get_loaders())
        napixd = NapixdBottle(loader=loader, server=server)

        return napixd

    def get_loaders(self):
        """
        Returns an array of :class:`napixd.loader.Importer`
        used to find the managers.
        """
        if 'test' in self.options:
            from napixd.loader.importers import FixedImporter
            return [FixedImporter({
                'root': 'napixd.examples.k132.Root',
                'host': (
                    'napixd.examples.hosts.HostManager', {
                        'file': '/tmp/h1'
                    })
            })]

        loaders = []

        if 'conf' in self.options:
            from napixd.loader.importers import ConfImporter
            ci = ConfImporter(self.conf.get('managers'), self.conf)
            loaders.append(ci)

        if 'auto' in self.options:
            from napixd.loader.auto import AutoImporter
            auto_path = get_path('auto')
            logger.info('Using %s as auto directory', auto_path)
            loaders.append(AutoImporter(auto_path))

        return loaders

    def install_plugins(self, router):
        """
        Install the plugins in the bottle application.
        """
        if 'time' in self.options:
            from napixd.plugins.times import TimePlugin
            router.add_filter(TimePlugin('x-total-time'))

        if 'times' in self.options:
            if not 'gevent' in self.options:
                raise CannotLaunch('`times` option requires `gevent`')
            from napixd.gevent_tools import AddGeventTimeHeader
            router.add_filter(AddGeventTimeHeader())

        if 'useragent' in self.options:
            from napixd.plugins.conversation import UserAgentDetector
            router.add_filter(UserAgentDetector())

        if 'auth' in self.options:
            self.auth_handler = self.get_auth_handler()
            router.add_filter(self.auth_handler)
        else:
            self.auth_handler = None

        return router

    def get_hostnames(self):
        hosts = self.conf.get('hosts')
        if not hosts:
            logger.warning('Using old location of setting hosts inside auth')
            self.conf.get('auth.hosts')

        if isinstance(hosts, basestring):
            return [hosts]
        elif isinstance(hosts, list):
            if not all(isinstance(host, basestring) for host in hosts):
                logger.error('All values in hosts conf key are not strings')
                hosts = [h for h in hosts if isinstance(h, basestring)]

            if hosts:
                return hosts
            else:
                logger.error('hosts conf key is empty. Guessing instead.')
        elif 'localhost' in self.options:
            return ['localhost:{0}'.format(self.get_port())]

        import socket
        hostname = socket.gethostname()
        logger.warning('Cannot reliably determine the hostname, using hostname "%s"', hostname)
        return [hostname]

    def get_app(self):
        """
        Return the bottle application with the plugins added
        """
        from napixd.http.server import WSGIServer
        server = WSGIServer()
        self.install_plugins(server.router)
        napixd = self.get_napixd(server)

        # attach autoreloaders
        if 'reload' in self.options:
            from napixd.reload import Reloader
            Reloader(napixd).start()

        if 'notify' in self.options:
            from napixd.notify import Notifier
            conf = self.conf.get('notify')
            if not 'url' in conf:
                raise CannotLaunch('Notifier has no configuration options')

            logger.info('Set up notifier')
            self.notifier = notifier = Notifier(
                napixd, conf, self.service_name, self.hosts[0],
                self.conf.get('description'))
            notifier.start()
        else:
            self.notifier = None

        if 'docs' in self.options:
            from napixd.docs import DocGenerator
            self.doc = DocGenerator(self.loader)
        else:
            self.doc = None

        if 'webclient' in self.options:
            self.web_client = self.get_webclient()
            if self.web_client:
                self.web_client.setup_bottle(napixd.server)
        else:
            self.web_client = None

        return napixd.server

    def apply_middleware(self, application):
        """
        Add the WSGI middleware in the application.

        Return the decorated application
        """
        from napixd.plugins.middleware import (PathInfoMiddleware,
                                               CORSMiddleware,
                                               LoggerMiddleware,
                                               HTTPHostMiddleware,
                                               )
        if 'uwsgi' in self.options:
            application = PathInfoMiddleware(application)
        if 'cors' in self.options:
            application = CORSMiddleware(application)
        if 'hosts' in self.options:
            application = HTTPHostMiddleware(self.hosts, application)
        if 'logger' in self.options:
            application = LoggerMiddleware(application)

        from napixd.plugins.exceptions import ExceptionsCatcher
        application = ExceptionsCatcher(
            application,
            show_errors=('print_exc' in self.options),
            pprint='pprint' in self.options)

        return application

    def get_application(self):
        """
        Returns the wsgi application.
        """
        self._patch_gevent()
        application = self.get_app()
        application = self.apply_middleware(application)
        if self.options.unchecked:
            self.logger.warning('Unchecked Options are: %s',
                                ','.join(self.options.unchecked))
        return application

    def get_server(self):
        """
        Get the bottle server adapter
        """
        if 'gevent' in self.options:
            from napixd.gevent_tools import GeventServer
            return GeventServer
        elif 'uwsgi' in self.options:
            raise CannotLaunch('The server cannot run on its own with uwsgi option')
        else:
            from napixd.wsgiref import WSGIRefServer
            return WSGIRefServer

    def get_host(self):
        if 'localhost' in self.options:
            return '127.0.0.1'
        return self.DEFAULT_HOST

    def get_port(self):
        return self.keys.port

    def get_server_options(self):
        self.server = server = self.get_server()
        server_options = {
            'host': self.get_host(),
            'port': self.get_port(),
            'server': server,
            'quiet': 'logger' in self.options,
        }
        if not 'gevent' in self.options:
            if server_options['quiet']:
                from napixd.wsgiref import QuietWSGIRequestHandler
                server_options['handler_class'] = QuietWSGIRequestHandler
                server_options['quiet'] = False
            else:
                from napixd.wsgiref import WSGIRequestHandler
                server_options['handler_class'] = WSGIRequestHandler

        return server_options

    def get_webclient(self):
        webclient_path = self.get_webclient_path()
        if not webclient_path:
            logger.warning('No webclient path found')
            return

        from napixd.webclient import WebClient
        logger.info('Using %s as webclient', webclient_path)
        return WebClient(webclient_path, self,
                         generate_docs='docs' in self.options)

    def get_webclient_path(self):
        """
        Retrieve the web client interface statics path.
        """
        module_file = sys.modules[self.__class__.__module__].__file__
        directories = [
            self.conf.get('webclient.path'),
            get_path('web', create=False),
            os.path.join(os.path.dirname(module_file), 'web'),
            os.path.join(os.path.dirname(__file__), 'web'),
        ]
        for directory in directories:
            logger.debug('Try WebClient in directory %s', directory)
            if directory and os.path.isdir(directory):
                return directory

    def set_loggers(self):
        """
        Defines the loggers
        """
        formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')

        self.log_file = file_handler = logging.handlers.RotatingFileHandler(
            self.LOG_FILE,
            maxBytes=5 * 10 ** 6,
            backupCount=10,
        )
        file_handler.setLevel(
            logging.DEBUG
            if 'verbose' in self.options else
            logging.WARNING
            if 'silent' in self.options else
            logging.INFO)
        file_handler.setFormatter(formatter)

        self.console = console_handler = logging.StreamHandler()
        console_handler.setLevel(
            logging.DEBUG
            if 'verbose' in self.options else
            logging.WARNING
            if 'silent' in self.options else
            logging.INFO)

        console_handler.setFormatter(formatter)

        logging.getLogger('Napix').setLevel(logging.DEBUG)
        logging.getLogger('Napix').addHandler(console_handler)
        logging.getLogger('Napix').addHandler(file_handler)

        if 'silent' not in self.options:
            if 'verbose' in self.options:
                logging.getLogger('Napix.console').setLevel(logging.DEBUG)
            else:
                logging.getLogger('Napix.console').setLevel(logging.INFO)
            logging.getLogger('Napix.console').addHandler(
                logging.StreamHandler())
