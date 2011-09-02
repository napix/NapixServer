#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
#import rpdb2; rpdb2.start_embedded_debugger('secret')

logging.basicConfig(filename='/tmp/napix.log', filemode='w', level=logging.DEBUG)
logging.getLogger('Rocket.Errors').setLevel(logging.INFO)

from bottle import ServerAdapter
from threadator import threadator
import bottle
import sys
import traceback
"""
from cStringIO import StringIO
"""
from plugins import ConversationPlugin
from handler import registry
from views import Service
from executor import executor
import os
import functools

logger = logging.getLogger('Napix.Server')
plugin_logger = logging.getLogger('Napix.Plugin')

print os.getpid()

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
            server = Rocket((self.host, self.port),'wsgi',
                    { 'wsgi_app' : handler }, min_threads=1, max_threads=2,
                    queue_size=1)

            server.start(background=True)
            threadator.start()
            self.executor.run()
        except (MemoryError,KeyboardInterrupt):
            pass
        except Exception,e:
            logger.error('Caught %s (%s)',type(e).__name__,str(e))
            a,b,c = sys.exc_info()
            traceback.print_exception(a,b,c)
        logger.info('Ready to stop')
        server.stop()
        threadator.stop()
        self.executor.stop()


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

@napixd.get('/TAYST')
def TAYST():
    from threadator import threadator
    l=logging.getLogger('WADT')
    def wait_and_do_thing(thread):
        x=executor.create_job(['sleep','10'],discard_output=True)
        return x.wait()
    t =  threadator.do_async(wait_and_do_thing)
    return str(t.ident)

if __name__ == '__main__':
    bottle.debug(True)
    logger.info('Starting')
    bottle.run(napixd,
            host='127.0.0.9',port=8080,
            server=RocketAndExecute,
            executor=executor)
    logger.info('Stopping')

