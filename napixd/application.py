#!/usr/bin/env python
# -*- coding: utf-8 -*-

# FIXME : dire que c'est l'application a lancer avec bottle.
# Mettre un exemple de ligne de commande

import logging

logging.basicConfig(filename='/tmp/napix.log', filemode='w', level=logging.DEBUG)
logging.getLogger('Rocket.Errors').setLevel(logging.INFO)

import bottle

from napixd import settings
from napixd.loader import load,load_conf
from napixd.plugins import ConversationPlugin
from napixd.services import Service
from napixd.executor.bottle_adapter import RocketAndExecutor

logger = logging.getLogger('Napix.Server')

registry = {}
napixd = bottle.Bottle(autojson=False)
napixd.autojson=False

for manager in load(settings.MANAGERS_PATH,settings.MANAGERS,settings.BLACKLIST):
    config = load_conf(manager)
    service = Service(manager,config)
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

