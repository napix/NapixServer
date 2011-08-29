#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Queue import Queue,Empty
import subprocess

class Executor(object):
    def __init__(self):
        self.pending_jobs = Queue()
        self.alive = True

    def append(self,job):
        return_queue = Queue()
        self.pending_jobs.put((job,return_queue))

    def run(self):
        while self.alive:
            try:
                job,return_queue = self.pending_jobs.get(block=True,timeout=1)
            except Empty:
                continue
            shell = subprocess.Popen(job,stderr=open('/dev/null'),stdout=open('/dev/null'))
            return_queue.put(shell)
            del job,return_queue

    def stop(self):
        self.alive = False

executor = Executor()
