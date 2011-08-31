#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Queue import Queue,Empty
from cStringIO import StringIO
import subprocess
import select
from threading import Thread
import logging
import itertools
import time
import os
import fcntl

logger=logging.getLogger('Napix.Executor')
fnlogger=logging.getLogger('Napix.Function')

class ExecutorQueue(Queue):
    def get(self,block=True,timeout=None):
        res=Queue.get(self,block,timeout)
        if isinstance(res,Exception):
            raise res
        return res

class Executor(object):
    def __init__(self,exec_manager):
        self.pending_jobs = Queue()
        self.manager= exec_manager
        self.alive = True

    def append(self,job):
        logger.debug('Registering job %s',id(job))
        return_queue = ExecutorQueue()
        self.pending_jobs.put((job,return_queue))
        return return_queue

    def run(self):
        self.manager.start()
        logger.info('Starting listenning %s',os.getpid())
        while self.alive:
            try:
                job,return_queue = self.pending_jobs.get(block=True,timeout=1)
                logger.debug('Found job %s',id(job))
            except Empty:
                continue
            try:
                handler = self.manager.append(job)
                fnlogger.debug('return queue 2')
                return_queue.put(handler)
            except Exception,e:
                fnlogger.debug('return queue 1')
                return_queue.put(e)
            del job,return_queue

    def stop(self):
        self.alive = False
        self.manager.stop()


class ExecManager(Thread):
    def __init__(self):
        super(ExecManager,self).__init__(name="exec_manager")
        self.poller = select.epoll()
        self.running_processes = {}
        self.running_handles = {}
        self.closed_handles = {}
        self.alive = True

    def stop(self):
        self.alive = False

    def __getitem__(self,item):
        try:
            return self.running_handles[item]
        except KeyError:
            return self.closed_handles[item]

    def __contains__(self,item):
        return item in self.running_handles or item in self.closed_handles

    def keys(self):
        x= []
        x.extend(self.running_handles.keys())
        x.extend(self.closed_handles.keys())
        return x

    def append(self,job):
        handle = ExecHandle(job)
        self.running_handles[handle.pid] = handle
        process = handle.process

        self._register(process.stdout,handle.read_stdout)
        self._register(process.stderr,handle.read_stderr)

        logger.debug('Appending %s job:%s pid:%s out:%s err:%s',
                subprocess.list2cmdline(job),
                id(job),handle.pid,process.stdout.fileno(),process.stderr.fileno())

        return handle

    def _register(self,stream,read_cb):
        self.running_processes[stream.fileno()]=read_cb
        self.poller.register(stream,select.EPOLLIN)
        fd = stream.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def _unregister(self,fd):
        os.fdopen(fd).close()
        self.poller.unregister(fd)
        del self.running_processes[fd]

    def run(self):
        while self.alive:
            for fd,event in self.poller.poll(timeout=1):
                if event & select.EPOLLIN:
                    logger.debug('%s gaves something',fd)
                    Thread(None,self.running_processes[fd],name="epoll event").start()
                if event & select.EPOLLHUP:
                    logger.debug('%s gaves SIGHUP',fd)
                    self._unregister(fd)

class ExecHandle(object):
    BUFFER_SIZE = 1024
    def __init__(self,job):
        self.id = id(job)
        self.process = subprocess.Popen(job,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
        self.stdout = StringIO()
        self.stderr = StringIO()
    def read_stderr(self):
        logger.debug('read stderr %s',self.id)
        self.stderr.write(self.process.stderr.read())
    def read_stdout(self):
        logger.debug('read stdout %s',self.id)
        self.stdout.write(self.process.stdout.read())
    def __getattr__(self,name):
        return getattr(self.process,name)

exec_manager = ExecManager()
executor = Executor(exec_manager)
