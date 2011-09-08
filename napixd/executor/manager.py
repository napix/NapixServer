#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import fcntl
import logging
from threading import Thread,Lock
from select import select
from napixd.executor.base import ExecStream,ExecutorRequest,ExecHandle
from cStringIO import StringIO

logger = logging.getLogger('Napix.ExecManager')

class ExecManager(Thread):
    """Manager that keep a trace of the activity of processes it got"""
    def __init__(self,executor):
        super(ExecManager,self).__init__(name="exec_manager")
        self.handles = Lock()
        self.running_handles = {}
        self.closed_handles = {}
        self.alive = True
        self.executor = executor

    def clean(self,process):
        """move the process from the running to the closed handles"""
        logger.debug('cleaning process %s'%process.pid)
        process.close()
        with self.handles:
            del self.running_handles[process.pid]
            self.closed_handles[process.pid] =  process

    def dispose(self,process):
        with self.handles:
            del self.closed_handles[process.pid]

    def stop(self):
        """stops the manager"""
        self.alive = False

    def __getitem__(self,item):
        """Get a managed process, either in the running handles or in the closed ones"""
        with self.handles:
            try:
                return self.running_handles[item]
            except KeyError:
                return self.closed_handles[item]

    def __contains__(self,item):
        """Return True if the process is in the managed process"""
        with self.handles:
            return item in self.running_handles or item in self.closed_handles

    def keys(self):
        """Get the PID of all the managed processes"""
        with self.handles:
            x= []
            x.extend(self.running_handles.keys())
            x.extend(self.closed_handles.keys())
            return x

    def create_job(self,job):
        """Add a process to manage"""
        request = ManagedHandle(job)
        handle = self.executor.append_request(request)
        self.running_handles[handle.pid] = handle

    def run(self):
        """
        Run the loop
        Check if the processes are still alive
        Get the processes that have a readable buffer and read them
        """
        while self.alive:
            streams = []
            for x in self.running_handles.values():
                streams.append(x.stdout)
                streams.append(x.stderr)
                logger.debug('Polling %s',x.pid)
                if x.poll() is not None:
                    self.clean(x)
            streams = filter(lambda x:isinstance(x,ExecStream),streams)
            if not streams:
                time.sleep(.2)
                continue
            for waiting_streams in select.select(streams,[],[],.1):
                for stream in waiting_streams:
                    stream.read()

class ManagedStream(ExecStream):
    def __init__(self,stream):
        super(ManagedHandle,self).__init__(stream)
        self.buff = StringIO()

        fd = self.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    def read(self):
        x = super(ManagedStream,self).read()
        self.buff.write(x)
        return x

class ManagedHandle(ExecHandle):
    stream_class = ManagedStream

class ManagedRequest(ExecutorRequest):
    handle_class = ManagedHandle
