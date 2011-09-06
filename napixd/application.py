#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

logging.basicConfig(filename='/tmp/napix.log', filemode='w', level=logging.DEBUG)
logging.getLogger('Rocket.Errors').setLevel(logging.INFO)

import os
import sys

import bottle

from napixd import settings
from napixd.plugins import ConversationPlugin
from napixd.views import Service
from napixd.executor_bottle import RocketAndExecutor
from napixd.base import BaseHandler,check_handler

logger = logging.getLogger('Napix.Server')

print os.getpid()


registry = {}
napixd = bottle.app.push()
for module_name in settings.HANDLERS:
    __import__(module_name)
    module = sys.modules[module_name]
    logger.debug('import %s',module)

    classes = [ getattr(module,x) for x in getattr(module,'__all__',dir(module))]
    logger.debug('found %s',classes)
    istype = lambda x:isinstance(x,type)
    ishandler = lambda x:(issubclass(x,BaseHandler))

    for handler in filter(lambda x:(istype(x) and ishandler(x)),classes):
        check_handler(handler)
        service = Service(handler)
        registry[service.url] = service
        service.setup_bottle(napixd)

napixd.install(ConversationPlugin())

if __name__ == '__main__':
    bottle.debug(settings.DEBUG)
    logger.info('Starting')
    bottle.run(napixd,
            host=settings.HOST,port=settings.PORT,
            server=RocketAndExecutor)
    logger.info('Stopping')

