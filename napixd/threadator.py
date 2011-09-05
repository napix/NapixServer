#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from time import time

from threading import Thread

from napixd.queue import SubQueue,Queue,Empty
logger = logging.getLogger('threadator')

__all__ = ['threadator','thread_manager','background_task']

class BackgroundTasker():
    def __init__(self,threadator):
        self.threadator =threadator
    def __call__(self,fn=None,**kw):
        def outer(fn):
            def inner(*args,**kwargs):
                return self.threadator.do_async(fn,args,kwargs,**kw)
            return inner
        if fn is None:
            return outer
        return outer(fn)

class ThreadManager(Thread):
    def __init__(self):
        Thread.__init__(self,name='threadator')
        self.process = {}
        self.activity = Queue()
        self.alive=True

    def do_async(self,*args,**kwargs):
        thread = ThreadWrapper(self.activity,*args,**kwargs)
        logger.debug('New Task')
        thread.start()
        self.process[thread.ident] = thread
        logger.debug('New Task %s',thread.ident)
        return thread

    def keys(self):
        return self.process.keys()
    def __getitem__(self,item):
        return self.process[item]

    def stop(self):
        self.alive = False

    def run(self):
        while self.alive:
            try:
                thread,ex_state=self.activity.get(timeout=1)
            except Empty:
                continue
            if ex_state != ThreadWrapper.CLOSED:
                continue
            logger.debug('Dead Task %s',thread.ident)
            del self.process[thread.ident]

class ThreadWrapper(Thread):
    CREATED,RUNNING,RETURNED,EXCEPTION,FINISHING,CLOSED = range(6)
    def __init__(self,activity,function,args=None,kwargs=None,on_success=None,on_failure=None,on_end=None):
        Thread.__init__(self)
        self.function = function
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.on_success = on_success or self._on_success
        self.on_failure = on_failure or self._on_failure
        self.on_end = on_end or self._on_end
        self._execution_state=self.CREATED
        self._status=''
        self.execution_state_queue=SubQueue(activity)
        self.start_time=None

    def run(self):
        self.start_time=time()
        try:
            self.execution_state = self.RUNNING
            result = self.function(self,*self.args,**self.kwargs)
        except Exception,e:
            self.execution_state = self.EXCEPTION
            self.on_failure(e)
        else:
            self.execution_state = self.RETURNED
            self.on_success(result)
        finally:
            self.execution_state = self.FINISHING
            self.on_end()
        self.execution_state = self.CLOSED
    def _on_end(self):
        pass
    def _on_failure(self,e):
        logger.warning('Thread %s Failed %s(%s)',self.ident,type(e).__name__,str(e))
    def _on_success(self,res):
        logger.info('Thread %s Succeeded %s(%s)',self.ident,type(res).__name__,repr(res))

    def _set_execution_state(self,value):
        self._execution_state = value
        self.execution_state_queue.put((self,value))
        logger.info('execution_state of %s changed %s',self.ident,value)

    def _get_execution_state(self):
        return self._execution_state
    execution_state = property(_get_execution_state,_set_execution_state)

    def _set_status(self,value):
        logger.debug('status of %s changed to %s',self.ident,value)
        self._status = value
    def _get_status(self):
        return self._status
    status = property(_get_status,_set_status)

thread_manager = ThreadManager()
threadator = thread_manager

background_task = BackgroundTasker(threadator)
