#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Queue import Queue
import subprocess

class Executor(object):
    def __init__(self):
        self.pending_jobs = Queue()

    def append(self,job):
        return_queue = Queue()
        self.pending_jobs.put((job,return_queue))

    def run(self):
        while True:
            job,return_queue = self.pending_jobs.get(block=True)
            shell = subprocess.Popen(job,stderr=open('/dev/null'),stdout=open('/dev/null'))
            return_queue.put(shell)
            del job,return_queue

executor = Executor()
