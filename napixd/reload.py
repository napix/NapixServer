#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import select
import logging
import gevent.select
import signal

import bottle

from napixd.conf import Conf

try:
    import pyinotify
except ImportError:
    pyinotify = None


logger = logging.getLogger()

class Poll(object):
    """Le poll du pauvre"""
    def __init__(self):
        self.fd = -1

    def register( self, fd, event):
        #event is select.POLLIN
        self.fd = fd

    def unregister(self):
        self.fd = -1

    def poll( self, timeout):
        if self.fd != -1:
            read, write, empty = gevent.select.select( [self.fd], [], [], timeout)
        return [ ( self.fd, select.POLLIN ) ]

def patch_select():
    if not hasattr( select, 'poll'):
        select.poll = Poll



class Reloader(object):

    def __init__(self, app ):
        self.app = app

    def start(self):
        signal.signal( signal.SIGHUP, self.on_sighup)
        self.app.route('/_napix_reload',callback=self.reload)

        logger.info( 'Launch Napix autoreloader')
        if pyinotify is not None:
            self.setup_inotify()
        else:
            logger.info('Did not find pyinotify, reload on file change support disabled')

    def setup_inotify(self):
        patch_select()
        watch_manager = pyinotify.WatchManager()
        for path in self.app.loader.paths:
            if os.path.isdir( path):
                watch_manager.add_watch( path, pyinotify.IN_CLOSE_WRITE)
        notifier = pyinotify.Notifier( watch_manager, self.on_file_change)
        gevent.spawn( notifier.loop)


    def on_sighup(self, signum, frame):
        logger.info('Caught SIGHUP, reloading')
        self.app.reload()

    def on_file_change( self, event):
        if ( event.dir or not event.name.endswith('.py')):
            return
        logger.info('Caught file change, reloading')
        self.app.reload()

    def reload( self):
        if not Conf.get_default().get('Napix.debug'):
            raise bottle.HTTPError( 403, 'Not in debug mode, HTTP reloading is not possible')
        logger.info('Asked to do so, reloading')
        self._reload()

