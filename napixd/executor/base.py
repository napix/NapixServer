#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
import os
import subprocess

from threading import Lock,current_thread
from napixd.queue import Queue,Empty,ThrowingSubQueue

logger=logging.getLogger('Napix.Executor')

__all__ = ['Executor']

"""
L'executor est une instance de la classe executor.
Il ne doit etre lancé qu'une seule instance d'executor simultanement

Interface Executor
    create_job(job:list(string),discard_output:bool) -> handler
        crée une requete de job, la depose dans la file d'attente
        et retourne le handler correspondant
        job:
            liste de strings qui represente la commande a executer
            et les arguments fournis
        discard_output:
            quand ce parametre est a True, la sortie standard du process
            sera redirigée vers /dev/null

    append_request(request) -> handler
        ajoute la requete request, la depose dans la file d'attente et
        retourne le handler
        append_request permet de spécifier une autre classe de requetes

    children_of(thread_id) -> list(wrapper)
        retourne tout les processus instanciés par le thread ayant pour id thread_id

    run()
        lance l'executor
        l'executor fourni deux fonctionalités: execute les requetes en attente
        et gere les threads qui ont terminé
        cette methode doit etre lancée dans le thread principal
    stop()
        termine l'executor;
        termine tout les processus actifs

Interface Handler
    les handlers sont des wrappers autour des process lancés.
    Ils notifient l'executor quand le process termine pour eviter les zombies

    Ils surchargent les methodes suivants
    poll() et wait()
        notifient l'executor de la fin d'un process
    kill()
        termine le process d'abord avec un SIGTERM et un SIGTERM 3 secondes plus tard
    close()
        ferme les flux stdout et stderr
    request
        object Request qui a initié le process

Interface Request
    take_ownership()
        le thread appelant cette methode devient le propriétaire du process
    owning_thread
        identifiant du thread qui a invoqué le process
    command
        retourne l'executable de la requete
    arguments
        retourne les arguments fournis a la fonction
    commandline
        retourne une chaine represetant la requete
    stdout et stderr
        flux d'erreur et de sortie standard

    exemple
    Request(['ls','-l','/home/user/my docs'])
    command = ls
    arguments = [-l,/home/user/my docs]
    commandline = ls -l "/home/user/my docs"

"""

class Executor(object):
    """
    object that listen in the main thread to a queue to get jobs
    to process and create process
    """
    def __init__(self):
        """Create some queues to dispatch jobs and events"""
        self.pending_jobs = Queue()
        self.activity = Queue()
        self.alive = True
        self.alive_processes = {}

    def create_job(self,job,discard_output=False):
        """Ask for job creation, the arguments are given to ExecutorRequest"""
        logger.debug('Registering job %s',id(job))
        request = ExecutorRequest(job,
                ThrowingSubQueue(self.activity), discard_output)
        return self.append_request(request)
    def append_request(self,request):
        self.pending_jobs.put(request)
        return request.return_queue.get()

    def run(self):
        """
        Start the depencies threads
        Run the main loop.
        Listen to the queue and open processes.
        """
        logger.info('Starting listenning %s',os.getpid())
        while self.alive:
            self._run_fork()
            self._run_owner()

    def _run_fork(self):
            try:
                request = self.pending_jobs.get(block=True,timeout=.1)
                logger.debug('Found job %s',id(request))
            except Empty:
                return
            try:
                handle = request.handle_class(request)
                request.return_queue.put(handle)
            except Exception,e:
                request.return_queue.put(e)
            del request

    def _run_owner(self):
            try:
                handle = self.activity.get(True,timeout=.1)
            except Empty:
                return
            if isinstance(handle,Exception):
                return
            if handle.returncode == None:
                self.alive_processes[handle.pid] = handle
            else:
                try:
                    del self.alive_processes[handle.pid]
                except KeyError:
                    #The process finished before the tracer got it
                    pass

    def children_of(self,tid):
        """Return the children of a thread"""
        return [x for x in self.alive_processes.values() if x.request.owning_thread == tid]

    def stop(self):
        """Stop the execution of the executor"""
        while not self.pending_jobs.empty():
            self.pending_jobs.get()
        self.alive = False

        logger.info('Kill them all, God will recognize his own')
        for process in self.alive_processes.values():
            process.kill()
        self.alive_processes = {}
        while not self.activity.empty():
            self.activity.get()

class ExecStream(object):
    """
    Proxy for a process' stream and a buffer
    Reading from the stream fill the buffer
    """
    def __init__(self,stream):
        """Proxy for the stream given as an argument"""
        self.stream = stream

    def read(self):
        """Try reading and if it success write in the buffer"""
        try:
            logger.debug('read stream %s',self.fileno())
            x= self.stream.read()
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

class ExecHandle(object):
    """Proxy to Popen"""

    stream_class = ExecStream
    def __init__(self,request):
        """
        Create the process for the givent request
        **This has to be run in the main thread**
        """
        self.request =  request
        outstream = request.discard_output and open('/dev/null','w') or subprocess.PIPE
        self.process = subprocess.Popen(request.job,stderr=outstream,stdout=outstream)
        if not request.discard_output:
            self.stdout = self.stream_class(self.process.stdout)
            self.stderr = self.stream_class(self.process.stderr)
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
                if self.poll() is not None:
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
            self.wait()

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

class ExecutorRequest(object):
    handle_class = ExecHandle
    """Request for a job to execute"""
    def __init__(self,job,return_queue,discard_output):
        """Create the request for *job*
        :param discard_output: boolean wich is True when you want the input to be redirected to /dev/null
        """
        self.job = job
        self.discard_output = discard_output
        self.take_ownership()
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


class NullStream(object):
    """Dummy stream when the output is discarded"""
    def close(self):
        pass
    def getvalue(self):
        return None
    def fileno(self):
        return -1
