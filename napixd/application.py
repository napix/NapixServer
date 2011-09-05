#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

logging.basicConfig(filename='/tmp/napix.log', filemode='w', level=logging.DEBUG)
logging.getLogger('Rocket.Errors').setLevel(logging.INFO)

import os
import sys
import functools

import bottle

from napixd import settings
from napixd.plugins import ConversationPlugin
from napixd.views import Service
from napixd.executor_bottle import ExecutorPlugin,RocketAndExecutor
from napixd.handler import BaseHandler

logger = logging.getLogger('Napix.Server')

print os.getpid()

def wrap(fn):
    @functools.wraps(fn)
    def inner(*args,**kwargs):
        logger.info('call wrap')
        return fn(bottle.request,*args,**kwargs)
    return inner


napixd = bottle.app.push()
for module_name in settings.HANDLERS:
    __import__(module_name)
    module = sys.modules[module_name]
    logger.debug('import %s',module)

    classes = [ getattr(module,x) for x in getattr(module,'__all__',dir(module))]
    istype = lambda x:isinstance(x,type)
    ishandler = lambda x:(issubclass(x,BaseHandler))

    for handler in filter(lambda x:(istype(x) and ishandler(x)),classes):
        service = Service(handler)
        ur = handler.url
        logger.debug('Installing %s at %s',handler,ur)
        napixd.route(r'/%s/:rid/:action_id'%ur,
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
    bottle.debug(settings.DEBUG)
    logger.info('Starting')
    bottle.run(napixd,
            host=settings.HOST,port=settings.PORT,
            server=RocketAndExecutor)
    logger.info('Stopping')

