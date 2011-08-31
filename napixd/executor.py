#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Queue import Queue,Empty
from cStringIO import StringIO
import subprocess
import select
from threading import Thread,Lock
import logging
import time
import os
import sys
import fcntl
import traceback

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

    def create_job(self,job,discard_output=False,managed=False):
        logger.debug('Registering job %s',id(job))
        return_queue = ExecutorQueue()
        self.pending_jobs.put((job,return_queue,discard_output,managed))
        return return_queue.get()

    def run(self):
        self.manager.start()
        logger.info('Starting listenning %s',os.getpid())
        while self.alive:
            try:
                job,return_queue,discard_output,managed = self.pending_jobs.get(block=True,timeout=1)
                logger.debug('Found job %s',id(job))
            except Empty:
                continue
            try:
                handler = ExecHandle(job,discard_output)
                if managed:
                    self.manager.add_hander(handler)
                fnlogger.debug('return queue 2')
                return_queue.put(handler)
            except Exception,e:
                fnlogger.debug('return queue 1')
                traceback.print_exception(*sys.exc_info())
                return_queue.put(e)
            del job,return_queue

    def stop(self):
        self.alive = False
        self.manager.stop()


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
    BUFFER_SIZE = 1024
    def __init__(self,job,discard_output):
        self.id = id(job)
        outstream = discard_output and open('/dev/null','w') or subprocess.PIPE
        self.process = subprocess.Popen(job,stderr=outstream,stdout=outstream)
        if not discard_output:
            self.stdout = ExecStream(self.process.stdout)
            self.stderr = ExecStream(self.process.stderr)
        else:
            self.stdout = NullStream()
            self.stderr = NullStream()
        self.closing=False
        self.closing_lock = Lock()
        self.command = subprocess.list2cmdline(job)

        logger.debug('Appending %s job:%s pid:%s out:%s err:%s',
                subprocess.list2cmdline(job),id(job),self.pid,
                self.stdout.fileno(),self.stderr.fileno())

    def kill(self):
        if self.process.returncode is not None:
            return True
        logger.info('KILL -15 %s',self.process.pid)
        self.process.terminate()
        for x in xrange(30):
            #wait 3seconds
            if self.process.poll() is not None:
                return True
            time.sleep(.1)
        logger.info('KILL -9 %s',self.process.pid)
        self.process.kill()
        return True

    def close(self):
        with self.closing_lock:
            if self.closing:
                return
            self.stderr.close()
            self.stdout.close()
            self.closing = True
            self.process.wait()

    def poll(self):
        return self.process.poll()

    @property
    def returncode(self):
        return self.process.returncode
    @property
    def pid(self):
        return self.process.pid

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

exec_manager = ExecManager()
executor = Executor(exec_manager)
