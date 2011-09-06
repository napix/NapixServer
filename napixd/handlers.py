#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import operator
import logging

from bottle import HTTPError

from napixd.handler import Handler,Value,action,SubHandler,IntIdMixin
from napixd.utils import run_command_or_fail,run_command,ValidateIf

from centrald.cas.models import Client
from pwd import getpwall,getpwuid,getpwnam
from grp import getgrall,getgrgid

from executor import executor
from threadator import thread_manager

logger = logging.getLogger('Napix.Handler')

__all__ = ['NAPIXAPI','RunningProcessHandler','ThreadManagerHandler','UnixAccountHandler','APIUserHandler','InitdHandler','UnixGroupHandler']

class NAPIXAPI(Handler):
    """Service d'introspection de API"""
    url = 'napix'

    doc = Value('documentation du handler')
    fields = Value('Champs disponibles dans les ressources')
    collection_methods = Value('Methodes applicable à la collection')
    resource_methods = Value('Methodes applicable à la ressource')
    actions =Value('Actions applicable à la ressource')

    @classmethod
    def find_all(cls):
        from napixd.application import registry
        return registry.keys()

    @classmethod
    def find(cls,rid):
        from napixd.application import registry
        try:
            handler = registry[rid]
        except KeyError:
            return None
        y={}
        y.update(handler.doc_resource)
        y.update(handler.doc_collection)
        y.update(handler.doc_action)
        return cls(rid,**y)

class RunningProcessHandler(IntIdMixin,Handler):
    """ asynchronous process handler """

    command = Value('command to be run')
    arguments = Value('args')
    discard_output = Value('disable stdout and stderr')
    returncode = Value('Return status of the process')
    stdout = Value('Standard output')
    stderr = Value('Error output')

    @classmethod
    def create(self,values):
        command = [ values.pop('command') ]
        command.extend(values.pop('arguments',[]))
        discard_output = bool(int(values.get('discard_output',True)))
        try:
            p = executor.create_job(command,discard_output,manager=True)
        except Exception,e:
            raise HTTPError(400,str(e))
        return p.pid

    @classmethod
    def find(cls,pid):
        try:
            process = executor.manager[pid]
        except KeyError:
            return None
        return cls(process)

    def __init__(self,process):
        self.rid = process.pid
        self.process = process

    def serialize(self):
        return {'rid':self.rid,
                'command':self.process.request.command,
                'arguments':self.process.request.arguments,
                'status': self.process.returncode is None and 'running' or 'finished',
                'returncode':self.process.returncode,
                'stderr' : self.process.stderr.getvalue(),
                'stdout': self.process.stdout.getvalue()
                }

    @classmethod
    def find_all(self):
        return executor.manager.keys()

    @action
    def kill(self):
        self.process.kill()
        return 'ok'

class ThreadManagerHandler(IntIdMixin,Handler):
    """Gestionnaire des taches asynchrones"""

    @classmethod
    def find_all(cls):
        return thread_manager.keys()

    @classmethod
    def find(cls,rid):
        try:
            return cls(thread_manager[rid])
        except KeyError:
            return None
    def __init__(self,thread):
        self.thread = thread
        self.spawned_process = executor.children_of(self.thread.ident)

    def serialize(self):
        return {
                'rid':self.thread.ident,
                'status':self.thread.status,
                'execution_state':self.thread.execution_state,
                'start_time':self.thread.start_time,
                'children' :
                [RunningProcessHandler(x).serialize() for x in self.spawned_process]
                }

class UnixGroupHandler(IntIdMixin,Handler):
    name = Value('Group name')

    @classmethod
    def find_all(cls):
        return map(operator.itemgetter(2),getgrall())

    def __str__(self):
        return self.name

    @classmethod
    def find(cls,rid):
        try:
            group = getgrgid(rid)
            inst = cls(rid,name=group.gr_name)
            inst.members = group.gr_mem
            return inst
        except KeyError:
            return None

class UnixAccountHandler(IntIdMixin,Handler):
    """Gestionnaire des comptes UNIX """
    table_pwd = { 'name' : 'login', 'gid': 'gid', 'gecos':'comment' ,'shell':'shell','dir':'home'}

    name = Value('Login')
    gid = Value('Groupe ID')
    gecos = Value('Commentaire')
    dir = Value('Répertoire personnel')
    shell = Value('Shell de login')

    def __str__(self):
        return self.name

    @classmethod
    def find(cls,uid):
        try:
            x= getpwuid(uid)
        except KeyError:
            return None
        self = cls(uid)
        for i in cls.fields:
            setattr(self,i,getattr(x,'pw_'+i))
        return self

    @classmethod
    def find_all(self):
        return map(operator.attrgetter('pw_uid'),getpwall())

    @classmethod
    def create(self,values):
        command = ['/usr/sbin/useradd']
        login = values.pop('name')
        for f,x in values.items():
            command.append('--'+self.table_pwd[f])
            command.append(x)
        command.append(login)
        code =  run_command(command)
        if code == 0:
             return getpwnam(login).pw_uid

    def modify(self,values):
        command = ['/usr/sbin/usermod']
        for f,x in values.items() :
            command.append('--'+self.table_pwd[f])
            command.append(x)
        command.append(self.name)
        run_command_or_fail(command)

    def remove(self,resource):
        run_command_or_fail(['/usr/sbin/userdel',resource['name']])

    class Group(SubHandler):
        handler = UnixGroupHandler

        @classmethod
        def find_all(cls,user):
            return map(operator.itemgetter(2),
                    filter(lambda x:user.name in x[3],getgrall()))
        @classmethod
        def find(cls,user,sid):
            group=cls.handler.find(sid)
            if not group or user.name not in group.members:
                return None
            return cls(user,group,sid)

        def remove(self):
            command = ['gpasswd']
            command.append('-d')
            command.append(self.resource.name)
            command.append(self.related.name)
            run_command_or_fail(command)

        @classmethod
        def create(self,user,group,values):
            command = ['gpasswd']
            command.append('-a')
            command.append(user.name)
            command.append(group.name)
            run_command_or_fail(command)
            return group.rid

class APIUserHandler(Handler):
    """Gestionnaire des utilisateurs de l'API"""

    secret = Value('Mot de passe')

    @classmethod
    def find(cls,uid):
        try:
            return cls(Client.objects.get(uid))
        except Client.DoesNotExist:
            return None

    @classmethod
    def find_all(cls):
        return Client.objects.values_list('pk',flat=True)

    @classmethod
    def create(self,values):
        return Client.objects.create(**values)

    def remove(self):
        self.client.delete()

    def modify(self,values):
        self.value = values.pop('secret')
        self.save()

    def __str__(self):
        return self.client.pk

    def __init__(self,client):
        self.client = client

    def serialize(self):
        return { 'rid':self.client.pk,'secret':self.client.value }

class InitdHandler(Handler):
    """ Gestionnaire des scripts init.d """

    path = '/etc/init.d'
    state = Value('Etat')

    @property
    def script(self):
         return os.path.join(self.path,self.rid)

    def modify(self,values):
        status = values['state'] == 'off' and 'stop' or 'start'
        run_command_or_fail([self.script,status])

    @classmethod
    @ValidateIf
    def validate_resource_id(cls,name):
        """ nom du daemon """
        return not '/' in name

    @classmethod
    def find_all(cls):
        return filter(lambda x:x[0]!='.',os.listdir(cls.path))

    @classmethod
    def find(cls,rid):
        path = os.path.join(cls.path,rid)
        if not os.path.isfile(path):
            return None
        running = (run_command([path,'status']) == 0)
        instance = cls(rid,state=running and 'on' or 'off')
        return instance

    @action
    def restart(self):
        """Restart the service"""
        run_command([self.script,'restart'])
