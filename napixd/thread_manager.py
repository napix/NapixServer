#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import functools
from time import time

from threading import Thread

from napixd.queue import SubQueue,Queue,Empty
logger = logging.getLogger('Napix.thread_manager')

__all__ = ['thread_manager','background']

"""
Les classes ThreadManager et BackgroundDecorator ne sont pas sensées etre utilisées directement.
Une instance de la classe ThreadManager est crée sous le nom de thread_manager. Une instance de
la classe BackgroundDecorator utilisant ce thread_manager est crée sous le nom de background.
Le tread_manager repose sur un thread de controle chargé de superviser les threads créés.

background est un décorateur permettant d'executer une fonction arbitraire dans un autre thread.
L'appel a la fonction décorée retourne instantanement le Threadwrapper qui execute la fonction

Exemple
@background
def send_mail(users):
    for u in users:
        send_mail(user)

def view(request):
    send_mail(User.objects.all()) #retourne immediatement

Le decorateur background peux prendre les arguments suivants, qui doivent être imperativement passés par mot-clé :
    give_thread:
        le thread_manager peut envoyer l'instance du thread wrapper comme premier
        argument de la fonction executé. par default, il est a False
    on_success,on_failure,on_end:
        voir do_async

Exemple
@background(give_thread=True,on_success=send_mail_ok)
def send_mail(thread,users):
    total = len(users)
    for idx,u in enumerate(users):
        thread.status = idx/total*100.
        send_mail(user)

def view(request):
    thread = send_mail(User.objects.all()) #retourne immediatement
    while thread.execution_state != 'CLOSED':
        print '%d %% mail sent '% thread.status

Le thread_manager permet de lancer des fonctions de manière asynchrone (ie: dans un thread séparé)
Il est possible de définir des callbacks qui seront appelés suivant l'evolution de l'execution du thread.
La fonction recupère une reference sur le thread et peux mettre a jour un statut dont le type est laissé
à la discretion du programmeur

Interface thread_manager
    do_async(fn:callable,<params>) -> thread
    il prends un argument obligatoire
        fn(thread,*fn_args,**fn_kwargs)
            callable qui sera executé de manière asynchrone
            cette fonction prends comme premier paramètre le ThreadWrapper dans lequel le thread
            s'executera, lui permettant ainsi de mettre a jour son status via thread.status
    do_async peut prendre en parametre optionnels
    callbacks:
        on_success(result)
            appelé si la fonction fini sans avoir produit d'exception.
            result est le resultat de l'execution du script
        on_failure(exception)
            appelé si la fonction jete une exception, prends en parametre
            l'exception jetée.
        on_end()
            appelé quand la fonction a fini quelque soit le resultat.
    lancement:
        fn_args
            tuple d'arguments passé a l'execution de la fonction
        fn_kwargs
            dictionnaire de mot clés passé à la fonction

De plus, le thread_manager garde trace de l'ensemble des fonction asynchrone (ie, les threads) qui sont en train
d'etre executée en emulant un dictionnaire.
Les clés sont les identificants des threads et les valeurs sont les instance de ThreadWrapper correspondante
>>> thread_manager[<thread_id>]
<ThreadWrapper instance XXXX>
>>> thread_manager.keys()
[ id1, id2, ... ]

Le thread manager demarre et arrete son thread de controle avec les metodes suivantes
    start()
        demarre le thread_manager
    stop()
        arrete le thread_manager dans la seconde qui suit. Les thread encore en cours continuent.

Le resultat de l'appel a do_async est un ThreadWrapper qui encapsule le thread pour lui donner accès
à des fonctionalités de controle.
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
        wrapper = thread_manager.do_aync(mail,args=(User.objects.all(),)) # retourne immediatement
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

"""

class BackgroundDecorator(object):
    """
    Instance of BackgroundDecorator can be used to decorate
    a function. When this function will be called, it will
    be in background in another thread.

    FIXME : remettre un exemple
    """
    def __init__(self,thread_manager):
        """
        init the background task with a thread_manager
        The thread_manager will be used to create the threads.
        """
        self.thread_manager =thread_manager
    def __call__(self,fn=None,give_thread=False,**kw):
        """
        function called when decorating a function
        returns a callable that will transmit its parameter
        to the function in the other thread
        The keywords provided to the decorator will be transmitted to the thread_manager
        ex: on_end,on_success,etc
        FIXME : reecrit ca en francais, la on ne comprends rien :)
        Dans un premier temps, decrire a quoi servent les parametres.
        S'il y a des trucs magiques (genre on_end, on_success) catché par **kw, dire ou est ce
        qu'on peut en recuperer la liste.

        Mettre un exemple de code en décrivant le comportement.
        """
        # FIXME : utiliser comme nom :
        # - decorator (pour le decorateur generer)
        # - wrapped (pour la fonction qui wrappe la fonction fn)
        
        def outer(fn):
            @functools.wraps(fn)
            def inner(*args,**kwargs):
                if not give_thread:
                    def droper(*args,**kwargs):
                        return fn(*args[1:],**kwargs)
                    fn = droper
                #real function call
                return self.thread_manager.do_async(fn,args,kwargs,**kw)
            return inner
        if fn is None:
            #if the decorator is called with keywork arguments
            # FIXME moi pas comprendre. Dire ce que tu m'as dit a l'oral, en citant
            # l'exemple : cas ou on est appelé en @pouet(...)
            # FIXME : et puis du coup, il se passe quoi si la fonction utilisateur utilise la variable fn
            # ou ne nome pas ses arguments ?
            return outer
        # FIXME ici on est appele en @pouet
        return outer(fn)

class ThreadManager(Thread):
    """Manager that follow the threads activity
    FIXME : c'est a dire ? quelles sont les taches précise de ce manager ?
    Est ce qu'il termine les process ? lit stdout ? Quel est la maniere de l'appeler.

    Mettre un exemple (ou plusieur) petit exemple (quitte a reprendre ceux du module en haut)
    """
    def __init__(self):
        Thread.__init__(self,name='thread_manager')
        self.active_threads = {}
        #FIXME : a quoi sert cette queue ?
        self.activity = Queue()
        self.alive=True

    def do_async(self,*args,**kwargs):
        """
        function called to do something in background
        parameters are given to ThreadWrapper
        FIXME : osef d'ou vont les parametres, qu'est ce que cela fait précisement ?
        
        En pratique, si ce truc sert a créé une instance de Threadwrapper a la volée et a
        l'executer, le préciser ainsi.

        Dire aussi ce qu'il advient du thread une fois lancé (est ce que le fait qu'il soit
        retourné a la fin impose des manipulations ?)
        """
        thread = ThreadWrapper(self.activity,*args,**kwargs)
        logger.debug('New Task')
        thread.start()
        self.active_threads[thread.ident] = thread
        logger.debug('New Task %s',thread.ident)
        return thread

    def keys(self):
        """return the active_threads' identity (thread.ident)"""
        return self.active_threads.keys()
    
    def __getitem__(self,item):
        """return the thread that is identified by *item*"""
        return self.active_threads[item]

    def stop(self):
        #FIXME : rajouter un parametre forced qui butte tout les threads fils a off par defaut
        """ stop the thread_manager """
        self.alive = False

    def run(self):
        """Main loop"""
        while self.alive:
            try:
                #get the activity
                thread,ex_state=self.activity.get(timeout=1)
            except Empty:
                continue
            # FIXME : pourquoi on fait cela ? 
            if ex_state != 'CLOSED':
                continue
            # FIXME : elle est dead la task, ou alors on est aussi dans ce cas la quand elle s'est arrete proprement ?
            logger.debug('Dead Task %s',thread.ident)
            #clean the finished thread
            del self.active_threads[thread.ident]

class ThreadWrapper(Thread):
    """ThreadWrapper is a proxy to the running thread"""
    STATUS = set(['CREATED','RUNNING','RETURNED','EXCEPTION','FINISHING','CLOSED'])
    def __init__(self,activity,
            function,fn_args=None,fn_kwargs=None,give_thread=False,
            on_success=None,on_failure=None,on_end=None):
        """
        FIXME : a quoi serve tout ces parametres ?
        Il y a manifestement des trucs par defaut pour _on_XXX, donc préciser le comprotement par defaut.

        S'il y a des parametres fixé pour les callback, les citer, et faire un exemple. (peu etre dans la doc de la classe)
        """
        Thread.__init__(self)

        self.execution_state_queue=SubQueue(activity)
        self.start_time=None

        # Set user provided function to run and arguments.
        self.function = function
        self.args = fn_args or ()
        if give_thread:
            self.args = ( self, ) + self.args
        self.kwargs = fn_kwargs or {}

        # Set callbacks
        self.on_success = on_success or self._on_success
        self.on_failure = on_failure or self._on_failure
        self.on_end = on_end or self._on_end

        #execution status initialized
        self._set_execution_state('CREATED')
        self._status=''

    def run(self):
        """Launch the thread"""
        self.start_time=time()
        try:
            self.execution_state = 'RUNNING'
            result = self.function(*self.args,**self.kwargs)
        except Exception,e:
            self.execution_state = 'EXCEPTION'
            #failure callback
            tmp = self.on_failure(e)
        else:
            self.execution_state = 'RETURNED'
            #success callback
            tmp = self.on_success(result)
        finally:
            self.execution_state = 'FINISHING'
            #end callback
            self.on_end(tmp)
        #finished
        self.execution_state = 'CLOSED'
    def _on_end(self,x):
        """dummy event handler"""
        pass
    def _on_failure(self,e):
        """dummy failure event """
        logger.warning('Thread %s Failed %s(%s)',self.ident,type(e).__name__,str(e))
    def _on_success(self,res):
        """dummy success event """
        logger.info('Thread %s Succeeded %s(%s)',self.ident,type(res).__name__,repr(res))

    def _set_execution_state(self,value):
        """
        Execution state setter
        Also send the execution_state to the activity queue
        """
        assert value in self.STATUS
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

#decorator
background = BackgroundDecorator(thread_manager)
