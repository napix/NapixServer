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
    """Request for a job to execute"""
    def __init__(self,job,return_queue,discard_output,managed):
        """Create the request for *job*
        :param discard_output: boolean wich is True when you want the input to be redirected to /dev/null
        :param managed: boolean wich is True when the process will be managed by another thread
        """
        self.job = job
        self.discard_output = discard_output
        self.take_ownership()
        self.managed = managed
        self.return_queue = return_queue
        logger.debug('Thread %s requested job %s',self.owning_thread,id(self))

    def take_ownership(self):
        """Set the current thread as the owner of the process"""
        self.owning_thread  = current_thread().ident

    @property
    def command(self):
        """Get the executable of the process"""
        return self.job[0]
    @property
    def arguments(self):
        """Get the arguments given to the executable"""
        return self.job[1:]
    @property
    def commandline(self):
        """Get the full command line"""
        return subprocess.list2cmdline(self.job)


class Executor(object):
    """
    object that listen in the main thread to a queue to get jobs
    to process and create process
    """
    def __init__(self):
        """Create some queues to dispatch jobs and events"""
        self.pending_jobs = Queue()
        self.activity = Queue()
        self.manager = ExecManager()
        self.owner_tracer = OwnerTracer(self.activity)
        self.alive = True

    def create_job(self,job,discard_output=False,managed=False):
        """Ask for job creation, the arguments are given to ExecutorRequest"""
        logger.debug('Registering job %s',id(job))
        request = ExecutorRequest(job, ThrowingSubQueue(self.activity),
                discard_output,managed)
        self.pending_jobs.put(request)
        return request.return_queue.get()

    def run(self):
        """
        Start the depencies threads
        Run the main loop.
        Listen to the queue and open processes.
        """
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
        """Return the children of a thread"""
        return self.owner_tracer.children_of(tid)

    def stop(self):
        """Stop the execution of the executor"""
        while not executor.pending_jobs.empty():
            executor.pending_jobs.get()
        self.alive = False
        self.manager.stop()
        self.owner_tracer.stop()

class OwnerTracer(Thread):
    """Trace the jobs runnings and the thead that asked them"""
    def __init__(self,activity_queue):
        """initialize the tracer, with the queue it will listen to"""
        self.activity = activity_queue
        self.alive=True
        self.alive_processes = {}
        Thread.__init__(self,name="OwnerTracer")

    def stop(self):
        """stop the tracer and kill the remaining processes"""
        self.alive = False
        logger.info('Kill them all, God will recognize his own')
        for process in self.alive_processes.values():
            process.kill()
        self.alive_processes = {}
        while not self.activity.empty():
            self.activity.get()

    def children_of(self,tid):
        """Get the running children of a thread"""
        return [x for x in self.alive_processes.values() if x.request.owning_thread == tid]

    def run(self):
        """run the main loop"""
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
    """Manager that keep a trace of the activity of processes it got"""
    def __init__(self):
        super(ExecManager,self).__init__(name="exec_manager")
        self.handles = Lock()
        self.running_handles = {}
        self.closed_handles = {}
        self.alive = True

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

    def add_hander(self,handle):
        """Add a process to manage"""
        self.running_handles[handle.pid] = handle
        return handle

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

class ExecHandle(object):
    """Proxy to Popen"""
    def __init__(self,request):
        """
        Create the process for the givent request
        **This has to be run in the main thread**
        """
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
        """
        Kill the process
        Send SIGTERM, wait 3 seconds and send SIGKILL
        """
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
        """Close the stream"""
        with self.closing_lock:
            if self.closing:
                return
            self.stderr.close()
            self.stdout.close()
            self.closing = True
            self.process.wait()

    def wait(self):
        """Wait for the process to complete and send the returncode in the activity queue"""
        res = self.process.wait()
        self.request.return_queue.put(self)
        return res
    def poll(self):
        """Poll for the process and send the returncode in the activity queue if any"""
        res = self.process.poll()
        if res is not None:
            self.request.return_queue.put(self)
        return res

    def __getattr__(self,attr):
        """ Proxy"""
        return getattr(self.process,attr)

class ExecStream(object):
    """
    Proxy for a process' stream and a buffer
    Reading from the stream fill the buffer
    """
    def __init__(self,stream):
        """Proxy for the stream given as an argument"""
        self.stream = stream
        self.buff = StringIO()

        fd = self.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def read(self):
        """Try reading and if it success write in the buffer"""
        try:
            logger.debug('read stream %s',self.fileno())
            x= self.stream.read()
            self.buff.write(x)
            return x
        except IOError:
            logger.warning('read stream %s failed',self.fileno())
    def close(self):
        """Close the stream"""
        self.stream.close()
    def fileno(self):
        """proxy method"""
        return self.stream.fileno()
    def getvalue(self):
        """Close the stream"""
        return self.buff.getvalue()

class NullStream(object):
    """Dummy stream when the output is discarded"""
    def close(self):
        pass
    def getvalue(self):
        return None
    def fileno(self):
        return -1

executor = Executor()

popen = executor.create_job
