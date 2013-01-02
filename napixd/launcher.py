#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import os
import sys
import bottle

import napixd

from napixd.loader import NapixdBottle
from napixd.conf import Conf
from napixd.plugins import ConversationPlugin, ExceptionsCatcher, AAAPlugin, UserAgentDetector
from napixd.reload import Reloader


logger = logging.getLogger('Napix.Server')
console = logging.getLogger('Napix.console')

def launch(options):
    sys.stdin.close()
    Setup(options).run()

class Setup(object):
    DEFAULT_HOST='localhost'
    DEFAULT_PORT=8002
    DEFAULT_OPTIONS = set([
        'app', #Launch the application
        'notify', # the thread of periodic notifications
        'doc', # the autodocumentation generation
        'useragent', # the html page shown when a browser access directly
        'auth', # the auth interface
        'reload', #the reloader on signal page and automatic
        'webclient', # the web client,
        #'executor', #The executor
        'gevent', #Use gevent
    ])

    LOG_FILE =  '/tmp/napix.log'
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
    notify:     Enable the notification thread
    doc:        Run the automatic documentation generation
    useragent:  The html page shown when a browser access directly
    auth:       The authentication component
    reload:     The reloader events attachement on signal, page and inotify
    webclient:  The web interface accessible on /_napix_js/
    executor:   Launch the executor controler
    gevent:     Use gevent as the wsgi interface

Non-default:
    silent:     Do not show the messages in the console
    debug:      Run the DEBUG mode
    print_exc:  Show the exceptions in the console output
    rocket:     Use Rocket as the server
    times:      Add custom header to show the running time and the total time
        '''
    def __init__(self, options):
        nooptions = [ opt[2:] for opt in options if opt.startswith('no') ]

        options = set(options)
        if 'only' not in options:
            options = options.union( self.DEFAULT_OPTIONS )
        self.options = options = options.difference( nooptions)

        self.set_loggers()

        console.info( 'Napixd Home is %s', napixd.HOME)
        console.info( 'Options are %s', ','.join(self.options))
        console.info( 'Starting process %s', os.getpid())
        console.info( 'Found napixd home at %s', napixd.HOME)
        console.info( 'Logging activity in %s', self.LOG_FILE )

        if 'gevent' in self.options:
            from gevent.monkey import patch_all
            patch_all()


    def run( self):
        if 'help' in self.options:
            print self.HELP_TEXT
            return 1
        if 'options' in self.options:
            print 'Enabled options are: ' + ' '.join( self.options)
            return

        app = self.get_app()
        server = self.get_server()

        logger.info('Starting')
        try:
            if 'app' in self.options :
                server_options = self.get_server_options()
                server_options['server'] = server
                bottle.run( app, **server_options)
        finally:
            console.info('Stopping')
            app.stop();

        console.info('Stopped')

    def set_debug(self):
        bottle.debug( 'debug' in self.options )

    def set_auth_handler(self, app):
        conf =  Conf.get_default('Napix.auth')
        if conf :
            app.install(AAAPlugin( conf, allow_bypass='debug' in self.options))
        else:
            logger.warning('No authentification configuration found.')

    def get_app(self):
        """
        Return the bottle application for the napixd server.
        """
        napixd = NapixdBottle( options=self.options)

        if 'useragent' in self.options:
            napixd.install( UserAgentDetector() )

        if 'auth' in self.options:
            self.set_auth_handler( napixd)

        #attach autoreloaders
        if 'reload' in self.options:
            Reloader( napixd).start()

        if 'times' in self.options:
            from napixd.gevent_tools import AddGeventTimeHeader
            napixd.install( AddGeventTimeHeader())

        napixd.install(ConversationPlugin())

        napixd.install(ExceptionsCatcher( show_errors=( 'print_exc' in self.options)))
        return napixd

    def get_settings(self):
        return dict( Conf.get_default().get('Napix.daemon'))

    def get_server(self):
        if 'gevent' in self.options:
            return 'gevent'
        elif 'rocket' in self.options:
            return 'rocket'

    def get_server_options(self):
        settings = self.get_settings()
        return {
                'host':settings.get('host', self.DEFAULT_HOST),
                'port':settings.get('port', self.DEFAULT_PORT),
                }

    def set_loggers(self):
        formatter = logging.Formatter( '%(levelname)s:%(name)s:%(message)s')
        self.log_file = file_handler = logging.FileHandler( self.LOG_FILE, mode='a')
        file_handler.setLevel( logging.INFO)
        file_handler.setFormatter( formatter)

        self.console = console_handler = logging.StreamHandler( )
        console_handler.setLevel(
                logging.DEBUG
                if 'verbose' in self.options else
                logging.WARNING
                if 'silent' in self.options else
                logging.INFO)

        console_handler.setFormatter( formatter)

        logging.getLogger('Rocket').addHandler( file_handler)
        logging.getLogger('Rocket').setLevel( logging.DEBUG )
        logging.getLogger('Rocket.Errors').setLevel(logging.DEBUG)
        logging.getLogger('Rocket.Errors.ThreadPool').setLevel(logging.INFO)

        logging.getLogger('Napix').setLevel( logging.DEBUG )
        logging.getLogger('Napix').addHandler( console_handler )
        logging.getLogger('Napix').addHandler( file_handler )

        if 'silent' not in self.options:
            if 'verbose' in self.options:
                logging.getLogger('Napix.console').setLevel( logging.DEBUG)
            else:
                logging.getLogger('Napix.console').setLevel( logging.INFO)
            logging.getLogger('Napix.console').addHandler( logging.StreamHandler() )



