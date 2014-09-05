#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging

import napixd
from napixd import get_file, get_path, __version__
from napixd.conf import Conf, ConfLoader, BaseConf
from napixd.utils.tracingset import TracingSet

logger = logging.getLogger('Napix.Server')
console = logging.getLogger('Napix.console')


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
        'recursive',  # Load sub directories of auto
        'conf',
        'time',  # Show duration
        'logger',  # Ouput of the logs in the console is consistent
        'docs',
        'dotconf',
        'central',  # Use a central Napix server for the authentication
        'colors',
        'cwd',
    ])

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
    recursive:  Load recursively from HOME/auto/ sub directories
    conf:       Load from the Napix.managers section of the config
    time:       Add custom header to show the duration of the request
    logger:     Standardize the ouptut on the console accross servers
    docs:       Generate automated documentation
    dotconf:    Use a dotconf file as the source of configuration
    central:    Use a central Napix server for the authentication
    colors:     Show colored logs in the console

Non-default:
    uwsgi:      Use with uwsgi
    gunicorn:   Use with gunicorn
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
    loggers:    Set up extra loggers
    logfile:    Write the log of Napix in a log file
    wait:       Do not respond in less than a given time
    ratelimit-auth: Enable the rate-limiting plugin by authenticated username
    ratelimit-ip:   Enable the rate-limiting plugin by source IP
    cwd:        Auto loader on the current working directory

Meta-options:
    only:       Disable default options
    help:       Show this message and quit
    options:    Show the enabled options and quit
'''

    def __init__(self, options, **keys):
        self.keys = keys
        nooptions = [opt[2:] for opt in options if opt.startswith('no')]

        options = set(options)
        if 'only' not in options:
            options = options.union(self.DEFAULT_OPTIONS)
        self.options = options = TracingSet(options.difference(nooptions))

        self.extra_web_client = {}
        self.set_loggers()

        self.conf = self.get_conf()

        if 'loggers' in self.options:
            self.set_extra_loggers()

        self.service_name = self.get_service_name()
        self.hosts = self.get_hostnames()

        console.info('Napix version %s', __version__)
        console.info('Napixd Home is %s', get_path())
        console.info('Options are %s', ','.join(sorted(self.options)))
        console.info('Starting process %s', os.getpid())
        console.info('Service Name is %s', self.service_name)

    def get_conf(self):
        """
        Get the configuration from the configuration file.

        It set the default conf instance by calling :meth:`napixd.conf.BaseConf.set_default`.
        """
        logger.info('Loading configuration')
        paths = [
            get_path('conf/'),
        ]
        if 'dotconf' in self.options:
            try:
                from napixd.conf.confiture import ConfFactory
            except ImportError:
                raise CannotLaunch('dotconf option requires the external library confiture')
            factory = ConfFactory()
        else:
            from napixd.conf.json import CompatConfFactory
            factory = CompatConfFactory()

        loader = ConfLoader(paths, factory)
        try:
            conf = loader()
        except ValueError as e:
            raise CannotLaunch('Cannot load conf: {0}'.format(e))

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
            print 'Enabled options are: ' + ' '.join(sorted(self.options))
            return

        self._patch_gevent()
        app = self.get_app()

        console.info('Starting')
        try:
            if 'app' in self.options:
                server_options = self.get_server_options()
                application = self.apply_middleware(app)

                console.info('Listening on %s:%s',
                             server_options['host'], server_options['port'])

                adapter_class = server_options.pop('server', None)
                if not adapter_class:
                    raise CannotLaunch('No server available')

                adapter = adapter_class(server_options)

                if self.options.unchecked:
                    console.warning('Unchecked Options are: %s',
                                    ','.join(sorted(self.options.unchecked)))
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
            central_provider = CentralAuthProvider.from_settings(self.service_name, conf)
            providers.append(central_provider)
            self.extra_web_client['auth_server'] = central_provider.host
            logger.info('Enable central server authentication')

        return providers

    def get_auth_sources(self, conf):
        from napixd.auth.sources import (
            SecureAuthProtocol,
            NonSecureAuthProtocol,
        )
        sources = [SecureAuthProtocol()]
        if 'secure' not in self.options:
            sources.append(NonSecureAuthProtocol.from_settings(conf))
            logger.info('Enable authentication by tokens')
        if 'jwt' in self.options:
            from napixd.auth.jwt import JSONWebToken
            sources.append(JSONWebToken())
        return sources

    def get_napixd(self, router):
        """
        Return the main application for the napixd server.
        """
        from napixd.application import Napixd
        from napixd.loader import Loader
        self.loader = loader = Loader(self.get_loaders())
        napixd = Napixd(loader, router)

        return napixd

    def get_loaders(self):
        """
        Returns an array of :class:`napixd.loader.Importer`
        used to find the managers.
        """
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

        if 'recursive' in self.options:
            from napixd.loader.auto import RecursiveAutoImporter
            auto_path = get_path('auto')
            loaders.append(RecursiveAutoImporter(auto_path))

        if 'cwd' in self.options:
            from napixd.loader.auto import RecursiveAutoImporter
            loaders.append(RecursiveAutoImporter(os.getcwd()))

        return loaders

    def install_plugins(self, router):
        """
        Install the plugins in the bottle application.

        .. note:: The plugins installed firsts are executed last.
        """
        if 'time' in self.options:
            from napixd.plugins.times import TimePlugin
            router.add_filter(TimePlugin('x-total-time'))

        if 'times' in self.options:
            if 'gevent' not in self.options:
                raise CannotLaunch('`times` option requires `gevent`')
            from napixd.gevent_tools import AddGeventTimeHeader
            router.add_filter(AddGeventTimeHeader())

        if 'useragent' in self.options:
            from napixd.plugins.conversation import UserAgentDetector
            router.add_filter(UserAgentDetector())

        if 'ratelimit-auth' in self.options:
            from napixd.plugins.ratelimit import (
                RateLimiterPlugin,
                RequestEnvironCriteria,
            )
            router.add_filter(RateLimiterPlugin.from_settings(
                self.conf.get('rate_limit.auth'),
                RequestEnvironCriteria('napixd.auth.username'),
            ))

        if 'auth' in self.options:
            auth_handler = self.get_auth_handler()
            router.add_filter(auth_handler)

        if 'ratelimit-ip' in self.options:
            from napixd.plugins.ratelimit import (
                RateLimiterPlugin,
                RequestEnvironCriteria,
            )
            router.add_filter(RateLimiterPlugin.from_settings(
                self.conf.get('rate_limit.ip'),
                RequestEnvironCriteria('REMOTE_ADDR'),
            ))

        if 'wait' in self.options:
            from napixd.plugins.times import WaitPlugin
            wait = self.conf.get('wait', 1000, type=(float, int))
            logger.info('Waiting for %sms', wait)
            router.add_filter(WaitPlugin(wait))

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
        router = self.install_plugins(server.push())
        napixd = self.get_napixd(router)

        # attach autoreloaders
        if 'reload' in self.options:
            from napixd.reload import Reloader
            Reloader(napixd).start()

        if 'notify' in self.options:
            from napixd.notify import Notifier
            conf = self.conf.get('notify')
            if 'url' not in conf:
                raise CannotLaunch('Notifier has no configuration options')

            logger.info('Set up notifier')
            self.notifier = notifier = Notifier(
                napixd, conf, self.service_name, self.hosts[0],
                self.conf.get('description'))
            notifier.start()
            self.extra_web_client['directory_server'] = notifier.directory
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
                self.web_client.setup_bottle(server)
        else:
            self.web_client = None

        return server

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
        if 'gunicorn' in self.options:
            application = PathInfoMiddleware(application, key='RAW_URI')
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
            logger.warning('Unchecked Options are: %s',
                           ','.join(sorted(self.options.unchecked)))
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
        return self.keys.get('port') or self.DEFAULT_PORT

    def get_server_options(self):
        self.server = server = self.get_server()
        server_options = {
            'host': self.get_host(),
            'port': self.get_port(),
            'server': server,
            'quiet': 'logger' in self.options,
        }
        if 'gevent' not in self.options:
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
            logger.error('No webclient path found')
            raise CannotLaunch('Option webclient is enabled but there is not webclient path')

        from napixd.webclient import WebClient
        logger.info('Using %s as webclient', webclient_path)
        return WebClient(webclient_path, self.get_webclient_infos(), docs=self.doc,
                         index=self.conf.get('webclient.index', 'index.html', type=unicode))

    def get_webclient_infos(self):
        infos = {
            'name': self.service_name,
            'version': __version__,
        }
        infos.update(self.extra_web_client)
        return infos

    def get_webclient_path(self):
        """
        Retrieve the web client interface statics path.
        """
        module_file = sys.modules[self.__class__.__module__].__file__
        directories = [
            self.conf.get('webclient.path'),
            get_path('web', create=False),
            os.path.join(os.path.dirname(module_file), 'web'),
            os.path.join(os.path.dirname(napixd.__file__), 'web'),
        ]
        for directory in directories:
            logger.debug('Try WebClient in directory %s', directory)
            if directory and os.path.isdir(directory):
                return directory

    def get_log_file(self):
        if hasattr(self, 'LOG_FILE'):
            import warnings
            warnings.warn('Use get_log_file instead of LOG_FILE')
            return self.LOG_FILE
        return get_file('log/napix.log')

    def get_logger_file(self):
        import logging.handlers
        lf = self.get_log_file()
        file_handler = logging.handlers.RotatingFileHandler(
            lf,
            maxBytes=5 * 10 ** 6,
            backupCount=10,
        )
        console.info('Writing logs in %s', lf)

        formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        return file_handler

    def get_logger_console_formatter(self):
        if 'colors' in self.options:
            from napixd.utils.logger import ColoredLevelFormatter
            return ColoredLevelFormatter('%(levelname)8s [%(name)s] %(message)s')
        else:
            return logging.Formatter('%(levelname)8s [%(name)s] %(message)s')

    def get_logger_console(self):
        formatter = self.get_logger_console_formatter()
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)

        return console_handler

    def get_loggers(self):
        log_handlers = []
        if 'silent' not in self.options:
            ch = self.get_logger_console()
            log_handlers.append(ch)
        if 'logfile' in self.options:
            lfh = self.get_logger_file()
            log_handlers.append(lfh)

        return log_handlers

    def set_loggers(self):
        """
        Defines the loggers
        """
        self.set_log_console()
        from napixd.utils.logger import NullHandler

        logger = logging.getLogger('Napix')
        logger.setLevel(logging.DEBUG if 'verbose' in self.options else logging.INFO)
        self.log_handlers = self.get_loggers() or [NullHandler()]

        for lh in self.log_handlers:
            logger.addHandler(lh)

    def set_log_console(self):
        console.setLevel(logging.DEBUG)
        if 'silent' in self.options:
            from napixd.utils.logger import NullHandler
            h = NullHandler()
        else:
            h = logging.StreamHandler()
            console.propagate = False
        console.addHandler(h)

    def set_extra_loggers(self):
        loggers = self.conf.get('loggers')

        if not loggers:
            logger.debug('No extra loggers')
            return

        for ns, level_name in loggers.items():
            if ns == 'logger' and isinstance(level_name, BaseConf):
                ns, level_name = level_name.get('name'), level_name.get('level')

            logger.info('Adding %s at level %s', ns, level_name)
            l = logging.getLogger(ns)
            level = getattr(logging, level_name.upper(), None)
            if not level:
                logger.error('Level %s does not exists', level)
                continue
            l.propagate = False
            l.setLevel(level)
            for lh in self.log_handlers:
                l.addHandler(lh)
