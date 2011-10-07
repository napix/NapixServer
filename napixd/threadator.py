#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import functools
from time import time

from threading import Thread

from napixd.queue import SubQueue,Queue,Empty
logger = logging.getLogger('threadator')

__all__ = ['threadator','thread_manager','background_task']

"""
Un object threadator et un object bacground_task relié sont créés et doivent être utilisés

Threadator definie un objet qui permet de lancer simplement des fonctions de manière asynchrone
Il est possible de définir des callbacks qui seront appelés suivant l'evolution de l'execution du thread.
La fonction executé dispose d'une reference sur le thread et peux mettre a jour un statut.

Interface threadator
    do_async(fn:callable,<params>) -> thread
    il prends un argument obligatoire
        fn(thread,*args,**kwargs)
            callable qui sera executé de manière asynchrone
            cette fonction prends comme premier paramètre le ThreadWrapper dans lequel le thread s'executera
            et lui permet de mettre a jour son status
    do_async peut prendre en parametre optionnels
    callbacks:
        on_success(result)
            appelé si la fonction fini sans avoir produit d'exception.
            result est le resultat de l'execution du script
        on_failure(exception)
            appelé si la fonction jete une exception, prends en parametre
            l'exception jeté.
        on_end()
            appelé quand la fonction a fini quelque soit le resultat.
    lancement:
        args
            tuple d'arguments passé a l'execution de la fonction
        kwargs
            dictionnaire de mot clés passé à la fonction

Le threadator agit aussi comme un dictionnaire de tout les threads qui'il execute actuellement
il definit
    [ thread_id ] -> thread
        retourne le thread ayant l'identifiant thread_id
    keys -> thread[]
        retourne tout les identifiant de thread

Enfin le threadator s'intègre avec les autres composant du serveur web, il definit les methodes start et stop
    start()
        demarre le threadator
    stop()
        arrete le threadator dans la seconde qui suit. Les thread encore en cours continuent.

Le resultat de l'appel a do_async est un ThreadWrapper qui encapsule le thread pour lui donner accès
a des fonctionalités de controle.
Interface ThreadWrapper
    status
        sert de transport pour une valeur arbitraire fourni par la fonction asynchrone
        pour les autres threads.
        Exemple:
        def mail_everyone(thread,users):
            total = len(users)
            for idx,user in enumerate(users):
                thread.status = idx/total*100.
                mail(user)
        wrapper = threadator.do_aync(mail,args=(User.objects.all(),)) # retourne immediatement
        # wrapper.status va prendre le pourcentage de mails envoyés
    execution_state
        sert de transport pour l'état dans lequel le thread se trouve actulement
        Il peut prendre les valeurs suivant
            CREATED
                valeur initiale du thread
            RUNNING
                Un thread a été créé et la fonction lancée dedans
            RETURNED
                la fonction a retourné une valeur
                on_success va être appelé
            EXCEPTION
                la fontion a jeté une exception
                on_failure  va être appelé
            FINISHING
                la fonction a fini
                on_end va être appelé
            CLOSED
                le thread a fini

Les objects bacgroundtasker servent de décorateur pour une fonction arbitraire
les appels a cette fonction seront fait dans un autre thread

exemple

@bacground_task
def send_mail(users):
    for u in users:
        send_mail(user)

def view(request):
    send_mail(User.objects.all()) #retourne immediatement

Le decorator bacground_task peux prendre les arguments mot-clés suivant:
    drop_thread:
        par default le threadator envoie l'instance du thread wrapper comme premier
        argument de la fonction executé.
        ce paramètre permet de supprimer ce thread pour s'interfacer de manière plus transparente.
        Par default il est a True.
    args,kwargs,on_success,on_failure,on_end:
        voir do_async

"""

class BackgroundTasker(object):
    """
    Instance of BackgroundTasker can be used to decorate
    a function. When this function will be called, it will
    be in background in another thread.
    """
    def __init__(self,threadator):
        """
        init the background task with a threadator
        The threadator will be used to create the threads.
        """
        self.threadator =threadator
    def __call__(self,fn=None,drop_thread=True,**kw):
        """
        function called when decorating a function
        returns a callable that will transmit its parameter
        to the function in the other thread
        The keywords provided to the decorator will be transmitted to the threadator
        ex: on_end,on_success,etc
        """
        def outer(fn):
            @functools.wraps(fn)
            def inner(*args,**kwargs):
                if drop_thread:
                    def droper(*args,**kwargs):
                        return fn(*args[1:],**kwargs)
                    fn = droper
                #real function call
                return self.threadator.do_async(fn,args,kwargs,**kw)
            return inner
        if fn is None:
            #if the decorator is called with keywork arguments
            return outer
        return outer(fn)

class ThreadManager(Thread):
    """Manager that follow the threads activity"""
    def __init__(self):
        Thread.__init__(self,name='threadator')
        self.active_threads = {}
        self.activity = Queue()
        self.alive=True

    def do_async(self,*args,**kwargs):
        """
        function called to do something in background
        parameters are given to ThreadWrapper
        """
        thread = ThreadWrapper(self.activity,*args,**kwargs)
        logger.debug('New Task')
        thread.start()
        self.active_threads[thread.ident] = thread
        logger.debug('New Task %s',thread.ident)
        return thread

    def keys(self):
        """return the active_threads' ident"""
        return self.active_threads.keys()
    def __getitem__(self,item):
        """return the thread that is identified by *item*"""
        return self.active_threads[item]

    def stop(self):
        """ stop the threadator """
        self.alive = False

    def run(self):
        """Main loop"""
        while self.alive:
            try:
                #get the activity
                thread,ex_state=self.activity.get(timeout=1)
            except Empty:
                continue
            if ex_state != ThreadWrapper.CLOSED:
                continue
            logger.debug('Dead Task %s',thread.ident)
            #clean the finished thread
            del self.active_threads[thread.ident]

class ThreadWrapper(Thread):
    """ThreadWrapper is a proxy to the running thread"""
    #statuses
    CREATED,RUNNING,RETURNED,EXCEPTION,FINISHING,CLOSED = range(6)
    def __init__(self,activity,function,args=None,kwargs=None,on_success=None,on_failure=None,on_end=None):
        Thread.__init__(self)

        self.execution_state_queue=SubQueue(activity)
        self.start_time=None

        #function to run with its arguments
        self.function = function
        self.args = args or ()
        self.kwargs = kwargs or {}

        #callbacks
        self.on_success = on_success or self._on_success
        self.on_failure = on_failure or self._on_failure
        self.on_end = on_end or self._on_end

        #execution status initialized
        self._set_execution_state(self.CREATED)
        self._status=''

    def run(self):
        """Launch the thread"""
        self.start_time=time()
        try:
            self.execution_state = self.RUNNING
            result = self.function(self,*self.args,**self.kwargs)
        except Exception,e:
            self.execution_state = self.EXCEPTION
            #failure callback
            self.on_failure(e)
        else:
            self.execution_state = self.RETURNED
            #success callback
            self.on_success(result)
        finally:
            self.execution_state = self.FINISHING
            #end callback
            self.on_end()
        #finished
        self.execution_state = self.CLOSED
    def _on_end(self):
        """default ending event"""
        pass
    def _on_failure(self,e):
        """default failure event"""
        logger.warning('Thread %s Failed %s(%s)',self.ident,type(e).__name__,str(e))
    def _on_success(self,res):
        """default success event"""
        logger.info('Thread %s Succeeded %s(%s)',self.ident,type(res).__name__,repr(res))

    def _set_execution_state(self,value):
        """
        Execution state setter
        Also send the execution_state to the activity queue
        """
        self._execution_state = value
        self.execution_state_queue.put((self,value))
        logger.info('execution_state of %s changed %s',self.ident,value)

    def _get_execution_state(self):
        """ execution_state getter"""
        return self._execution_state
    execution_state = property(_get_execution_state,_set_execution_state)

    def _set_status(self,value):
        """status setter"""
        logger.debug('status of %s changed to %s',self.ident,value)
        self._status = value
    def _get_status(self):
        """status getter"""
        return self._status
    status = property(_get_status,_set_status)

#Thread manager instance
thread_manager = ThreadManager()
#thread_manager alias
threadator = thread_manager

#decorator
background_task = BackgroundTasker(threadator)
