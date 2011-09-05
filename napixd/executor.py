#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import fcntl

import logging
import os
import sys
import traceback

import subprocess
import select
from threading import Thread,Lock,current_thread
from queue import Queue,Empty,ThrowingSubQueue

from cStringIO import StringIO

logger=logging.getLogger('Napix.Executor')

__all__ = ['Executor','executor','popen']

class ExecutorRequest(object):
    def __init__(self,job,return_queue,discard_output,managed):
        self.job = job
        self.discard_output = discard_output
        self.take_ownership()
        self.managed = False
        self.return_queue = return_queue
        logger.debug('Thread %s requested job %s',self.owning_thread,id(self))

    def take_ownership(self):
        self.owning_thread  = current_thread().ident

    @property
    def command(self):
        return self.job[0]
    @property
    def arguments(self):
        return self.job[1:]
    @property
    def commandline(self):
        return subprocess.list2cmdline(self.job)


class Executor(object):
    def __init__(self):
        self.pending_jobs = Queue()
        self.activity = Queue()
        self.manager = ExecManager()
        self.owner_tracer = OwnerTracer(self.activity)
        self.alive = True

    def create_job(self,job,discard_output=False,managed=False):
        logger.debug('Registering job %s',id(job))
        return_queue = ThrowingSubQueue(self.activity)
        request = ExecutorRequest(job,return_queue,discard_output,managed)
        self.pending_jobs.put(request)
        return return_queue.get()

    def run(self):
        self.manager.start()
        self.owner_tracer.start()
        logger.info('Starting listenning %s',os.getpid())
        while self.alive:
            try:
                request = self.pending_jobs.get(block=True,timeout=1)
                logger.debug('Found job %s',id(request))
            except Empty:
                continue
            try:
                handler = ExecHandle(request)
                if request.managed:
                    self.manager.add_hander(handler)
                    request.take_ownership()
                request.return_queue.put(handler)
            except Exception,e:
                traceback.print_exception(*sys.exc_info())
                request.return_queue.put(e)
            del request

    def children_of(self,tid):
        return self.owner_tracer.children_of(tid)

    def stop(self):
        self.alive = False
        self.manager.stop()
        self.owner_tracer.stop()

class OwnerTracer(Thread):
    def __init__(self,activity_queue):
        self.activity = activity_queue
        self.alive=True
        self.alive_processes = {}
        Thread.__init__(self,name="OwnerTracer")

    def stop(self):
        self.alive = False
        logger.info('Kill them all, God will recognize his own')
        for process in self.alive_processes.values():
            process.kill()

    def children_of(self,tid):
        return [x for x in self.alive_processes.values() if x.request.owning_thread == tid]

    def run(self):
        while self.alive:
            try:
                handle = self.activity.get(True,timeout=1)
            except Empty:
                continue
            if isinstance(handle,Exception):
                continue
            if handle.returncode == None:
                self.alive_processes[handle.pid] = handle
            else:
                try:
                    del self.alive_processes[handle.pid]
                except KeyError:
                    #The process finished before the tracer got it
                    pass

class ExecManager(Thread):
    def __init__(self):
        super(ExecManager,self).__init__(name="exec_manager")
        self.handles = Lock()
        self.running_handles = {}
        self.closed_handles = {}
        self.alive = True

    def clean(self,process):
        logger.debug('cleaning process %s'%process.pid)
        process.close()
        with self.handles:
            del self.running_handles[process.pid]
            self.closed_handles[process.pid] =  process

    def dispose(self,process):
        with self.handles:
            del self.closed_handles[process.pid]

    def stop(self):
        self.alive = False

    def __getitem__(self,item):
        with self.handles:
            try:
                return self.running_handles[item]
            except KeyError:
                return self.closed_handles[item]

    def __contains__(self,item):
        with self.handles:
            return item in self.running_handles or item in self.closed_handles

    def keys(self):
        with self.handles:
            x= []
            x.extend(self.running_handles.keys())
            x.extend(self.closed_handles.keys())
            return x

    def add_hander(self,handle):
        self.running_handles[handle.pid] = handle
        return handle

    def run(self):
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

class ExecHandle(object):
    def __init__(self,request):
        self.request =  request
        outstream = request.discard_output and open('/dev/null','w') or subprocess.PIPE
        self.process = subprocess.Popen(request.job,stderr=outstream,stdout=outstream)
        if not request.discard_output:
            self.stdout = ExecStream(self.process.stdout)
            self.stderr = ExecStream(self.process.stderr)
        else:
            self.stdout = NullStream()
            self.stderr = NullStream()
        self.closing=False
        self.closing_lock = Lock()
        self.kill_lock = Lock()

        logger.debug('Appending %s job:%s pid:%s out:%s err:%s',
                request.commandline,id(request),self.pid,
                self.stdout.fileno(),self.stderr.fileno())

    def kill(self):
        with self.kill_lock:
            if self.returncode is not None:
                return
            logger.info('KILL -15 %s',self.process.pid)
            self.process.terminate()
            for x in xrange(30):
                #wait 3seconds
                if self.process.poll() is not None:
                    return
                time.sleep(.1)
            logger.info('KILL -9 %s',self.process.pid)
            self.process.kill()
            return

    def close(self):
        with self.closing_lock:
            if self.closing:
                return
            self.stderr.close()
            self.stdout.close()
            self.closing = True
            self.process.wait()

    def wait(self):
        res = self.process.wait()
        self.request.return_queue.put(self)
        return res
    def poll(self):
        res = self.process.poll()
        if res is not None:
            self.request.return_queue.put(self)
        return res

    def __getattr__(self,attr):
        return getattr(self.process,attr)

class ExecStream(object):
    def __init__(self,stream):
        self.stream = stream
        self.buff = StringIO()

        fd = self.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def read(self):
        try:
            logger.debug('read stream %s',self.fileno())
            x= self.stream.read()
            self.buff.write(x)
            return x
        except IOError:
            logger.warning('read stream %s failed',self.fileno())
    def close(self):
        self.stream.close()
    def fileno(self):
        return self.stream.fileno()
    def getvalue(self):
        return self.buff.getvalue()

class NullStream(object):
    def close(self):
        pass
    def getvalue(self):
        return None
    def fileno(self):
        return -1

executor = Executor()

popen = executor.create_job
