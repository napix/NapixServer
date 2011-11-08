#!/usr/bin/env python
# -*- coding: utf-8 -*-

# FIXME : dire que c'est l'application a lancer avec bottle.
# Mettre un exemple de ligne de commande

import logging

logging.basicConfig(filename='/tmp/napix.log', filemode='w', level=logging.DEBUG)
logging.getLogger('Rocket.Errors').setLevel(logging.INFO)

import bottle
from napixd.executor.bottle_adapter import RocketAndExecutor
from napixd.loader import get_bottle_app
from napixd.conf import Conf

if __name__ == '__main__':
    logger = logging.getLogger('Napix.Server')

    napixd = get_bottle_app()
    settings = dict( Conf.get_default().get('Napix.daemon'))

    bottle.debug(settings.get('debug',False))
    logger.info('Starting')

    bottle.run(napixd, host=settings.get('host','127.0.0.1'),
            port=settings.get('port',8080), server=RocketAndExecutor)

    logger.info('Stopping')

