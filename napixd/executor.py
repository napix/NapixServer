#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Queue import Queue,Empty
from cStringIO import StringIO
import subprocess
import select
from threading import Thread

class Executor(object):
    def __init__(self,exec_manager):
        self.pending_jobs = Queue()
        self.manager= exec_manager
        self.alive = True

    def append(self,job):
        return_queue = Queue()
        self.pending_jobs.put((job,return_queue))
        return return_queue

    def run(self):
        self.manager.start()
        while self.alive:
            try:
                job,return_queue = self.pending_jobs.get(block=True,timeout=1)
            except Empty:
                continue
            shell = subprocess.Popen(job,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
            return_queue.put(shell)
            self.manager.append(shell)
            del job,return_queue

    def stop(self):
        self.alive = False


class ExecManager(Thread):
    def __init__(self):
        super(ExecManager,self).__init__()
        self.poller = select.epoll()
        self.running_processes = {}
        self.running_handles = []
        self.closed_handles = []

    def append(self,process):
        handle = ExecHandle(process)
        self.running_handles =handle

        self.running_processes[process.stdout.fileno()]=handle.read_stdout
        self.running_processes[process.stderr.fileno()]=handle.read_stderr

        self.poller.register(process.stdout,select.EPOLLIN)
        self.poller.register(process.stderr,select.EPOLLIN)

    def run(self):
        while True:
            for fd,event in self.poller.poll(timeout=.1):
                if event & select.EPOLLIN:
                    Thread(None,self.running_processes[fd]).start()

class ExecHandle(object):
    BUFFER_SIZE = 1024
    def __init__(self,process,return_queue):
        self.process = process
        self.stdout = StringIO()
        self.stdin = StringIO()
    def read_stderr(self):
        self.stderr.write(self.process.stderr.read())
    def read_stdout(self):
        self.stdout.write(self.process.stdout.read())

exec_manager = ExecManager()
executor = Executor(exec_manager)
