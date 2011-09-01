#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Thread
from Queue import Queue
import logging
logger = logging.getLogger('ThreadWrapper')

class ThreadManager(object):
    def __init__(self):
        self.process = {}

    def do_async(self,*args,**kwargs):
        thread = ThreadWrapper(*args,**kwargs)
        logger.debug('New Task')
        self.wait_for(thread)
        thread.start()
        self.process[thread.ident] = thread
        logger.debug('New Task %s',thread.ident)
        return thread

    def keys(self):
        return self.process.keys()
    def __getitem__(self,item):
        return self.process[item]

    def wait_for(self,thread):
        def inner():
            while thread.execution_state != ThreadWrapper.CLOSED:
                thread.status_queue.get()
            logger.debug('Dead Task %s',thread.ident)
            del self.process[thread.ident]
        Thread(target=inner).start()

class ThreadWrapper(Thread):
    CREATED,RUNNING,RETURNED,EXCEPTION,FINISHING,CLOSED = range(6)
    def __init__(self,function,args=None,kwargs=None,on_success=None,on_failure=None,on_end=None):
        Thread.__init__(self)
        self.function = function
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.on_success = on_success or self._on_success
        self.on_failure = on_failure or self._on_failure
        self.on_end = on_end or self._on_end
        self._execution_state=self.CREATED
        self.status=''
        self.status_queue=Queue()

    def run(self):
        try:
            result = self.function(self,*self.args,**self.kwargs)
        except Exception,e:
            self.status = self.EXCEPTION
            self.on_failure(e)
        else:
            self.status = self.RETURNED
            self.on_success(result)
        finally:
            self.status = self.FINISHING
            self.on_end()
        self.status = self.CLOSED
    def _on_end(self):
        pass
    def _on_failure(self,e):
        logger.warning('Thread %s Failed %s(%s)',self.ident,type(e).__name__,str(e))
    def _on_success(self,res):
        logger.info('Thread %s Succeeded %s(%s)',self.ident,type(res).__name__,repr(res))

    def _set_execution_state(self,value):
        self._execution_state = value
        self.status_queue.put(value)
        logger.info('execution_state changed %s %s',self.ident,value)

    def _get_execution_state(self):
        return self._status
    execution_state = property(_get_execution_state,_set_execution_state)

    def _set_status(self,value):
        self._status = value
    def _get_status(self):
        return self._status
    status = property(_get_status,_set_status)

thread_manager = ThreadManager()
threadator = thread_manager
