#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import traceback
import functools

import bottle
from bottle import ServerAdapter

from napixd.executor import executor
from napixd.threadator import threadator

__all__ = ['RocketAndExecutor','ExecutorPlugin']

logger = logging.getLogger('Napix.Server')

class RocketAndExecutor(ServerAdapter):
    def run(self,handler):
        try:
            from rocket import Rocket
            server = Rocket((self.host, self.port),'wsgi',
                    { 'wsgi_app' : handler }, min_threads=1, max_threads=2,
                    queue_size=1)

            server.start(background=True)
            threadator.start()
            executor.run()
        except (MemoryError,KeyboardInterrupt,SystemError):
            pass
        except Exception,e:
            logger.error('Caught %s (%s)',type(e).__name__,str(e))
            a,b,c = sys.exc_info()
            traceback.print_exception(a,b,c)
        logger.info('Ready to stop')
        server.stop()
        threadator.stop()
        executor.stop()


class ExecutorPlugin(object):
    name = 'executor'
    api=2
    def __init__(self):
        self.executor = executor
    def apply(self,callback,route):
        @functools.wraps(callback)
        def inner(*args,**kwargs):
            request = bottle.request
            request.executor = self.executor
            return callback(*args,**kwargs)
        return inner

