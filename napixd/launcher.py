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

from napixd import get_file, get_path

from napixd.conf import Conf

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
    ])

    LOG_FILE = get_file('log/napix.log')
    HELP_TEXT = '''
napixd daemon runner.
usage: napixd [(no)option] ...
       napixd help: show this message
       napixd [only] [(no)option] ... options: show enabled options

option to enable the option.
nooptions to disable the option

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
    uwsgi:      Use with uwsgi
    auto:       Load from HOME/auto/ directory
    conf:       Load from the Napix.managers section of the config
    time:       Add custom header to show the duration of the request
    logger:     Standardize the ouptut on the console accross servers

Non-default:
    notify:     Enable the notification thread
    silent:     Do not show the messages in the console
    verbose:    Augment the ouptut of the loggers
    debug:      Run the DEBUG mode
    print_exc:  Show the exceptions in the console output
    rocket:     Use Rocket as the server
    times:      Add custom header to show the running time and the total time (requires gevent)
    pprint:     Enable pretty printing of output
    cors:       Add Cross-Site Request Service headers
    secure:     Disable the request tokeb signing
    localhost:  Listen on the loopback interface only

Meta-options:
    only:       Disable default options
    help:       Show this message and quit
    options:    Show the enabled options and quit
        '''

    def __init__(self, options):
        nooptions = [opt[2:] for opt in options if opt.startswith('no')]

        options = set(options)
        if 'only' not in options:
            options = options.union(self.DEFAULT_OPTIONS)
        self.options = options = options.difference(nooptions)

        self.set_loggers()
        self.service_name = self.get_service_name()

        console.info('Napixd Home is %s', get_path())
        console.info('Options are %s', ','.join(self.options))
        console.info('Starting process %s', os.getpid())
        console.info('Logging activity in %s', self.LOG_FILE)
        console.info('Service Name is %s', self.service_name)

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
        self.set_debug()
        app = self.get_app()

        logger.info('Starting')
        try:
            if 'app' in self.options:
                server_options = self.get_server_options()
                application = self.apply_middleware(app)

                import bottle
                bottle.run(application, **server_options)
        finally:
            console.info('Stopping')

        console.info('Stopped')

    def set_debug(self):
        import bottle
        bottle.debug('debug' in self.options)

    def get_service_name(self):
        """
        Returns the name of the service.

        This name is cache in :attr:`service_name`

        The configuration option ``Napix.auth.service`` is used.
        If it does not exists, the name is fetched from :file:`/etc/hostname`
        """
        service = Conf.get_default('Napix.auth.service')
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
        conf = Conf.get_default('Napix.auth')
        if not conf:
            raise CannotLaunch(
                '*auth* option is set and no configuration has been found (see Napix.auth key).')

        if 'secure' in self.options:
            from napixd.plugins.auth import AAAPlugin
            aaa_class = AAAPlugin
        else:
            logger.info('Installing not Secure auth plugin')
            from napixd.plugins.auth import NoSecureAAAPlugin
            aaa_class = NoSecureAAAPlugin

        return aaa_class(conf,
                         allow_bypass='debug' in self.options,
                         service_name=self.service_name,
                         with_chrono='time' in self.options,
                         )

    def get_bottle(self):
        """
        Return the bottle application for the napixd server.
        """
        from napixd.application import NapixdBottle
        from napixd.loader import Loader
        loader = Loader(self.get_loaders())
        napixd = NapixdBottle(loader=loader)
        self.install_plugins(napixd)

        return napixd

    def get_loaders(self):
        """
        Returns an array of :class:`napixd.loader.Importer`
        used to find the managers.
        """
        if 'test' in self.options:
            from napixd.loader import FixedImporter
            return [FixedImporter({
                'root': 'napixd.examples.k132.Root',
                'host': (
                    'napixd.examples.hosts.HostManager', {
                        'file': '/tmp/h1'
                    })
            })]

        from napixd.loader import AutoImporter, ConfImporter
        loaders = []

        if 'conf' in self.options:
            loaders.append(ConfImporter(Conf.get_default()))
        if 'auto' in self.options:
            auto_path = get_path('auto')
            logger.info('Using %s as auto directory', auto_path)
            loaders.append(AutoImporter(auto_path))
        return loaders

    def install_plugins(self, app):
        """
        Install the plugins in the bottle application.
        """
        if 'time' in self.options:
            from napixd.plugins.times import TimePlugin
            app.install(TimePlugin('x-total-time'))

        pprint = 'pprint' in self.options

        if 'times' in self.options:
            if not 'gevent' in self.options:
                raise CannotLaunch('`times` option requires `gevent`')
            from napixd.gevent_tools import AddGeventTimeHeader
            app.install(AddGeventTimeHeader())

        from napixd.plugins.exceptions import ExceptionsCatcher
        app.install(ExceptionsCatcher(
            show_errors=('print_exc' in self.options), pprint=pprint))

        from napixd.plugins.conversation import ConversationPlugin
        app.install(ConversationPlugin(pprint=pprint))

        if 'useragent' in self.options:
            from napixd.plugins.conversation import UserAgentDetector
            app.install(UserAgentDetector())

        return app

    def get_app(self):
        """
        Return the bottle application with the plugins added
        """
        napixd = self.get_bottle()

        if 'auth' in self.options:
            self.auth_handler = self.get_auth_handler()
            napixd.install(self.auth_handler)
        else:
            self.auth_handler = None

        # attach autoreloaders
        if 'reload' in self.options:
            from napixd.reload import Reloader
            Reloader(napixd).start()

        if 'webclient' in self.options:
            self.web_client = self.get_webclient()
            if self.web_client:
                self.web_client.setup_bottle(napixd)
        else:
            self.web_client = None

        if 'notify' in self.options:
            from napixd.notify import Notifier
            conf = Conf.get_default('Napix.notify')
            if not 'url' in conf:
                raise CannotLaunch('Notifier has no configuration options')

            logger.info('Set up notifier')
            notifier = Notifier(napixd, conf)
            notifier.start()

        return napixd

    def apply_middleware(self, application):
        """
        Add the WSGI middleware in the application.

        Return the decorated application
        """
        from napixd.plugins.middleware import (PathInfoMiddleware,
                                               CORSMiddleware,
                                               LoggerMiddleware)
        if 'uwsgi' in self.options:
            application = PathInfoMiddleware(application)
        if 'cors' in self.options:
            application = CORSMiddleware(application)
        if 'logger' in self.options:
            application = LoggerMiddleware(application)
        return application

    def get_application(self):
        """
        Returns the wsgi application.
        """
        self._patch_gevent()
        application = self.get_app()
        return self.apply_middleware(application)

    def get_server(self):
        """
        Get the bottle server adapter
        """
        if 'rocket' in self.options:
            return 'rocket'
        elif not 'gevent' in self.options:
            return 'wsgiref'
        elif 'uwsgi' in self.options:
            return 'gevent'
        else:
            from napixd.gevent_tools import GeventServer
            return GeventServer

    def get_host(self):
        if 'localhost' in self.options:
            return '127.0.0.1'
        return self.DEFAULT_HOST

    def get_port(self):
        return self.DEFAULT_PORT

    def get_server_options(self):
        """
        Returns a dict of the options of :func:`bottle.run`
        """
        self.server = server = self.get_server()
        server_options = {
            'host': self.get_host(),
            'port': self.get_port(),
            'server': server,
            'quiet': 'logger' in self.options,
        }
        if server == 'wsgiref':
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
        return WebClient(webclient_path, self)

    def get_webclient_path(self):
        """
        Retrieve the web client interface statics path.
        """
        module_file = sys.modules[self.__class__.__module__].__file__
        module_path = os.path.join(os.path.dirname(module_file), 'web')
        napix_default = os.path.join(os.path.dirname(__file__), 'web')
        for directory in [
                Conf.get_default('Napix.webclient.path'),
                get_path('web', create=False),
                module_path,
                napix_default,
        ]:
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

        if 'rocket' in self.options:
            logging.getLogger('Rocket').addHandler(file_handler)
            logging.getLogger('Rocket').setLevel(logging.DEBUG)
            logging.getLogger('Rocket.Errors').setLevel(logging.DEBUG)
            logging.getLogger(
                'Rocket.Errors.ThreadPool').setLevel(logging.INFO)

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
