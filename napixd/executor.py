#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Queue import Queue,Empty
from cStringIO import StringIO
import subprocess
import select
from threading import Thread,Lock
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
        self.running_handles = {}
        self.closed_handles = {}
        self.alive = True

    def terminate(self,process):
        logger.debug('cleaning process %s'%process.pid)
        del self.running_handles[process.pid]
        self.closed_handles[process.pid] =  process

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
        handle = ExecHandle(self,job)
        self.running_handles[handle.pid] = handle

        logger.debug('Appending %s job:%s pid:%s out:%s err:%s',
                subprocess.list2cmdline(job),id(job),handle.pid,
                handle.process.stdout.fileno(),handle.process.stderr.fileno())

        return handle

    def run(self):
        while self.alive:
            streams = []
            for x in self.running_handles.values():
                streams.append(x.stdout)
                streams.append(x.stderr)
            for waiting_streams in select.select(streams,[],[],1):
                for stream in waiting_streams:
                    stream.read()

class ExecHandle(object):
    BUFFER_SIZE = 1024
    def __init__(self,manager,job):
        self.id = id(job)
        self.manager = manager
        self.process = subprocess.Popen(job,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
        self.stdout = ExecStream(self,'stdout')
        self.stderr = ExecStream(self,'stderr')
        self.closing=False
        self.closing_lock = Lock()

    def close(self):
        with self.closing_lock:
            if self.closing:
                return
            self.closing = True
            self.manager.terminate(self)
            self.process.wait()

    def __del__(self):
        del self.manager

    def __getattr__(self,name):
        return getattr(self.process,name)

class ExecStream(object):
    def __init__(self,parent,stream):
        self.parent = parent
        self.stream = getattr(parent.process,stream)
        self.buff = StringIO()
        self.name = stream

        fd = self.stream.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def __del__(self):
        #help refcount
        del self.parent
    def read(self):
        logger.debug('read stream %s',self.name)
        x= self.stream.read()
        if not(x):
            self.parent.close()
        else:
            self.buff.write(x)
        return x
    def fileno(self):
        return self.stream.fileno()
    def getvalue(self):
        return self.buff.getvalue()

exec_manager = ExecManager()
executor = Executor(exec_manager)
