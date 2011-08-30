#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

logging.basicConfig(filename='/tmp/napix.log', filemode='w', level=logging.DEBUG)
logging.getLogger('Rocket.Errors').setLevel(logging.INFO)

from bottle import ServerAdapter
import bottle
import sys
import traceback
"""
from cStringIO import StringIO
import json
"""
from handler import registry
from views import Service
from executor import executor
import os
import functools

logger = logging.getLogger('Napix.Server')
plugin_logger = logging.getLogger('Napix.Plugin')

def wrap(fn):
    @functools.wraps(fn)
    def inner(*args,**kwargs):
        return fn(bottle.request,*args,**kwargs)
    return inner

class RocketAndExecute(ServerAdapter):
    def __init__(self,**kwargs):
        ServerAdapter.__init__(self,**kwargs)
        self.executor = kwargs.pop('executor')
    def run(self,handler):
        try:
            from rocket import Rocket
            print os.getpid()
            server = Rocket((self.host, self.port), 'wsgi', { 'wsgi_app' : handler })

            server.start(background=True)
            self.executor.run()
        except (MemoryError,KeyboardInterrupt):
            pass
        except Exception,e:
            logger.error('Caught %s (%s)',type(e).__name__,str(e))
            a,b,c = sys.exc_info()
            traceback.print_exception(a,b,c)
        logger.info('Ready to stop')
        server.stop()
        self.executor.stop()

class ConversationPlugin(object):
    name = "conversation_plugin"
    api = 2
    def apply(self,callback,route):
        plugin_logger.info('Installing %s',self.name)
        def inner(*args,**kwargs):
            plugin_logger.debug('%s running',self.name)
            request = bottle.request
            request.data = hasattr(request,'json') and request.json or request.forms
            res = callback(*args,**kwargs)
            if hasattr(res,'serialize'):
                return res.serialize()
            return res
        return inner

class ExecutorPlugin(object):
    name = 'executor'
    api=2
    def __init__(self):
        self.executor = executor
    def apply(self,callback,route):
        plugin_logger.info('Installing %s',self.name)
        def inner(*args,**kwargs):
            plugin_logger.debug('%s running',self.name)
            request = bottle.request
            request.executor = self.executor
            return callback(*args,**kwargs)
        return inner


import handlers
napixd = bottle.app.push()
for ur,handler in registry.items():
    service = Service(handler)
    napixd.route(r'/%s/:rid/:action_id/'%ur,
            callback=wrap(service.view_action),
            name='%s_action'%ur,
            method=['HEAD','GET','POST'])
    napixd.route(r'/%s/:rid'%ur,
            callback=wrap(service.view_resource),
            name='%s_resource'%ur,
            method=handler.resource_methods)
    napixd.route(r'/%s/'%ur,
            callback=wrap(service.view_collection),
            name='%s_collection'%ur,
            method=handler.collection_methods)
napixd.install(ConversationPlugin())
napixd.install(ExecutorPlugin())

if __name__ == '__main__':
    bottle.debug(True)
    logger.info('Starting')
    bottle.run(napixd,
            server=RocketAndExecute,
            executor=executor)
    logger.info('Stopping')

