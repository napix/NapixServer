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
from napixd.services import Service
from napixd.executor.bottle_adapter import RocketAndExecutor
from napixd.resources import Collection

logger = logging.getLogger('Napix.Server')

print os.getpid()


registry = {}
napixd = bottle.app.push()
for module_name in settings.HANDLERS:
    __import__(module_name)
    module = sys.modules[module_name]
    logger.debug('import %s',module)

    istype = lambda x:isinstance(x,type)
    ishandler = lambda x:(issubclass(x,Collection))
    classes = [ getattr(module,x) for x in getattr(module,'__all__',dir(module))]
    classes = [ x for x in classes if istype(x) and ishandler(x)]
    logger.debug('found %s',classes)

    for handler in classes:
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

