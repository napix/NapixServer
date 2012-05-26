#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import traceback

from bottle import ServerAdapter
from rocket import Rocket
from napixd.executor import executor

__all__ = ['RocketAndExecutor']

logger = logging.getLogger('Napix.Server')

class RocketAndExecutor(ServerAdapter):
    """Server adapter for bottle wich starts Rocket and start the executor"""
    def run(self,handler):
        """run the main loop"""
        server = Rocket((self.host, self.port),'wsgi',
                { 'wsgi_app' : handler }, min_threads=1, max_threads=2,
                queue_size=1)

        try:
            server.start(background=True)
            executor.run()
        except (MemoryError,KeyboardInterrupt,SystemError):
            pass
        except Exception,e:
            logger.error('Caught %s (%s)',type(e).__name__,str(e))
            a,b,c = sys.exc_info()
            traceback.print_exception(a,b,c)
        logger.info('Ready to stop')
        handler.stop()
        server.stop()
        executor.stop()

