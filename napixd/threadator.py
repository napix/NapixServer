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
Un object threadator et un object bacground_task relié sont créés et doivent être utilisés FIXME : il manque un bout de phrase

Threadator definie un objet simple qui permet de lancer des fonctions de manière asynchrone (ie; dans un thread séparé)
Il est possible de définir des callbacks qui seront appelés suivant l'evolution de l'execution du thread.
La fonction executée dispose d'une reference sur le thread et peux mettre a jour un statut.
FIXME : La fonction éxecutée se voit passer en paramêtre le thread, lui permettant ainsi de mettre a jour un status (si c'est fait
autrement, alors le résumer)

Interface threadator
    do_async(fn:callable,<params>) -> thread
    il prends un argument obligatoire
        fn(thread,*args,**kwargs)
            callable qui sera executé de manière asynchrone
            cette fonction prends comme premier paramètre le ThreadWrapper dans lequel le thread
            s'executera, lui permettant ainsi de mettre a jour son status via FIXME : thread.status ?
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
    lancement: FIXME : renomer ces parametres en fn_args et fn_kwargs ?
        args
            tuple d'arguments passé a l'execution de la fonction
        kwargs
            dictionnaire de mot clés passé à la fonction

De plus, le threadator garde trace de l'ensemble des fonction asynchrone (ie, les threads) qui sont en train
d'etre executée en emulant un dictionnaire.
FIXME : si les thread_id sont autre chose que des pid, le dire. Si ce sont des pid_, le dire quand meme.
Ainsi, on pourra executer :
>>> threadator[<thread_id>]
<threadWrapper instance XXXX> FIXME : mettre le nom du veritable objet
>>> threadator.keys()
[ "id1", "id2", ... ]
FIXME : si cala suffit, virer la suite (moins intelligible)

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
        FIXME : rajouter un parametre forced qui butte tout les threads fils a off par defaut

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
FIXME : La classe BackgroundTasker est automatiquement instanciée lors de l'import
        du module sous le nom de 'background_task'. Cet objet est ensuite à utiliser
        comme décorateur lorsque l'on souhaite que les appel a la fonction décorée
        soit réalisée automatiquement dans un autre thread.
        Il est a noté que de ce fait, la fonction sera executée en background, et
        que le code appelant ne recuperera pas ce qu'elle retourne. Si une action doit être
        executée avec le resultat, celle ci doit être précisé dans le callback on_success.

        FIXME : on ne retourne vraiment rien ? meme pas l'id du thread ?

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

    FIXME : remettre un exemple
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
                if drop_thread:
                    def droper(*args,**kwargs):
                        return fn(*args[1:],**kwargs)
                    fn = droper
                #real function call
                return self.threadator.do_async(fn,args,kwargs,**kw)
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
        Thread.__init__(self,name='threadator')
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
        FIXME : rajouter un parametre forced qui butte tout les threads fils a off par defaut
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
            # FIXME : pourquoi on fait cela ? 
            if ex_state != ThreadWrapper.CLOSED:
                continue
            # FIXME : elle est dead la task, ou alors on est aussi dans ce cas la quand elle s'est arrete proprement ?
            logger.debug('Dead Task %s',thread.ident)
            #clean the finished thread
            del self.active_threads[thread.ident]

class ThreadWrapper(Thread):
    """ThreadWrapper is a proxy to the running thread"""
    #Statuses FIXME : Y-a un interet a faire ca comme ca plutot que de maintenir un status en toute lettre ?
    # Genre STATUS = set(["CREATED", ...]) et on verifie juste quand on le set qu'on utilise bien un truc présent dans self.STATUS ?
    CREATED,RUNNING,RETURNED,EXCEPTION,FINISHING,CLOSED = range(6)
    def __init__(self,activity,function,args=None,kwargs=None,on_success=None,on_failure=None,on_end=None):
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
        self.args = args or ()
        self.kwargs = kwargs or {}

        # Set callbacks
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
            # FIXME : il pourrait être utile de recuperer l'output de on_success et de le renvoyer a on_end
            self.on_success(result)
        finally:
            self.execution_state = self.FINISHING
            #end callback
            self.on_end()
        #finished
        self.execution_state = self.CLOSED
    def _on_end(self):
        """default ending event FIXME : si cela ne fait rien, on dit "dummy""""
        pass
    def _on_failure(self,e):
        """default failure event FIXME"""
        logger.warning('Thread %s Failed %s(%s)',self.ident,type(e).__name__,str(e))
    def _on_success(self,res):
        """default success event FIXME"""
        logger.info('Thread %s Succeeded %s(%s)',self.ident,type(res).__name__,repr(res))

    def _set_execution_state(self,value):
        """
        Execution state setter
        Also send the execution_state to the activity queue
        """
        # FIXME : je pense qu'il serait sain de verifier que "value" est correct
        self._execution_state = value
        self.execution_state_queue.put((self,value))
        logger.info('execution_state of %s changed %s',self.ident,value)

    def _get_execution_state(self):
        """ execution_state getter"""
        return self._execution_state
    # FIXME : a quoi sert cette property ? (parametre doc="pouetpouet")
    execution_state = property(_get_execution_state,_set_execution_state)

    def _set_status(self,value):
        """status setter"""
        logger.debug('status of %s changed to %s',self.ident,value)
        self._status = value
        
    def _get_status(self):
        """status getter"""
        return self._status
    # FIXME : a quoi sert cette property ? (parametre doc="pouetpouet")
    status = property(_get_status,_set_status)


# FIXME : c'est quoi ces trucs ? Ca sert a être utilisé derriere sans se prendre la tete ?
# A priori les exemples les utiliseront, donc le mettre
# A noter que je ne suis pas sur que ce soit tres propre comme maniere de faire :) (mais bon
# ca osef)
#Thread manager instance
thread_manager = ThreadManager()
#thread_manager alias
threadator = thread_manager

#decorator
background_task = BackgroundTasker(threadator)
