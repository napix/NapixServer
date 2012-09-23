#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import operator
import os
import bottle

import napixd
from napixd.loader import get_bottle_app
from napixd.conf import Conf


LOG_FILE =  '/tmp/napix.log'

def segregate( segregator, iterable ):
    has = []
    hasnt = []
    for e in iterable:
        if segregator(e):
            has.append( e)
        else:
            hasnt.append(e)
    return has, hasnt

logger = logging.getLogger('Napix.Server')
console = logging.getLogger('Napix.console')

def launch(options):
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
        'executor', #The executor
    ])

    HELP_TEXT = '''
napixd daemon runner.
usage: napixd [(no)option] ...
       napixd help: show this message 
       napixd [(no)option] ... options: show enabled options

option to enable the option.
nooptions to disable the option
options are:
app:        Launch the application
notify:     Enable the notification thread
doc:        Run the automatic documentation generation
useragent:  The html page shown when a browser access directly
auth:       The authentication component
reload:     The reloader events attachement on signal, page and inotify
webclient:  The web interface accessible on /_napix_js/
executor:   Launch the executor controler
gevent:     Use gevent controller
silent:     Do not show the messages in the console
        '''
    def __init__(self, options):
        self.options = options
        nooptions, options = segregate( lambda x:x.startswith('no'), options)
        nooptions = map( operator.itemgetter( slice(2,None)), nooptions)
        self.options = set(options).union( self.DEFAULT_OPTIONS ).difference( nooptions)

        self.set_loggers()

        console.info( 'Napixd Home is %s', napixd.HOME)
        console.info( 'Options are %s', ','.join(options))
        console.info( 'Starting process %s', os.getpid())
        console.info( 'Found napixd home at %s', napixd.HOME)
        console.info( 'Logging activity in %s', LOG_FILE )


    def run( self):
        if 'help' in self.options:
            print self.HELP_TEXT
            return 1
        if 'options' in self.options:
            print 'Enabled options are: ' + ' '.join( self.options)
            return

        settings = self.get_settings()
        app = self.get_app()
        server = self.get_server()


        logger.info('Starting')
        try:
            if 'app' in self.options :
                bottle.run( app, host=settings.get('host', self.DEFAULT_HOST),
                        port=settings.get('port', self.DEFAULT_PORT), server=server)
        finally:
            logger.info('Stopping')
            app.stop();

        logger.info('Stopped')

    def set_debug(self):
        bottle.debug( 'debug' in self.options and Conf.get('Napix.debug',False))

    def get_app(self):
        return get_bottle_app( self.options)
    def get_settings(self):
        return dict( Conf.get_default().get('Napix.daemon'))
    def get_server(self):
        if 'executor' in self.options:
            from napixd.executor.bottle_adapter import RocketAndExecutor
            return RocketAndExecutor
        elif 'gevent' in self.options:
            return 'gevent'
        else:
            return 'rocket'

    def set_loggers(self):
        formatter = logging.Formatter( '%(levelname)s:%(name)s:%(message)s')
        file_handler = logging.FileHandler( LOG_FILE, mode='a')
        file_handler.setLevel( logging.DEBUG)
        file_handler.setFormatter( formatter)

        console_handler = logging.StreamHandler( )
        console_handler.setLevel( logging.WARNING )
        console_handler.setFormatter( formatter)

        logging.getLogger('Rocket').addHandler( file_handler)
        logging.getLogger('Rocket').setLevel( logging.DEBUG )
        logging.getLogger('Rocket.Errors').setLevel(logging.INFO)

        logging.getLogger('Napix').setLevel( logging.DEBUG )
        logging.getLogger('Napix').addHandler( console_handler )
        logging.getLogger('Napix').addHandler( file_handler )

        if 'silent' not in self.options:
            logging.getLogger('Napix.console').setLevel( logging.INFO )
            logging.getLogger('Napix.console').addHandler( logging.StreamHandler() )



