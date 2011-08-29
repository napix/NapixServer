#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiprocessing import Process
from subprocess import Popen
import tempfile
import operator
import os
from time import time

from pwd import getpwall,getpwuid,getpwnam
from napixd.exceptions import ValidationError
from napixd.utils import run_command_or_fail,run_command,ValidateIf

from handler import MetaHandler,Value,action,registry
from centrald.cas.models import Client

class NAPIXAPI(object):
    """Service d'introspection de API"""
    url = 'napix'
    __metaclass__ = MetaHandler

    doc = Value('documentation du handler')
    fields = Value('Champs disponibles dans les ressources')
    collection_methods = Value('Methodes applicable à la collection')
    resource_methods = Value('Methodes applicable à la ressource')
    actions =Value('Actions applicable à la ressource')

    @classmethod
    def find_all(cls):
        return registry.keys()

    @classmethod
    def find(cls,rid):
        try:
            handler = registry[rid]
        except KeyError:
            return None
        y={}
        y.update(handler.doc_resource)
        y.update(handler.doc_collection)
        y.update(handler.doc_action)
        return cls(rid,**y)

class RunningProcessHandler(object):
    """ asynchronous process handler """
    __metaclass__ = MetaHandler


    command = Value('command to be run')
    arguments = Value('args')
    return_code = Value('Return status of the process')

    tmp_dir = '/tmp/napix'
    if not os.path.isdir(tmp_dir):
        os.mkdir(tmp_dir,700)

    @classmethod
    def create(self,values):
        command = [ values.pop('command') ]
        command.extend(values.pop('arguments',[]))
        directory =tempfile.mkdtemp(dir=self.tmp_dir)
        out = open(os.path.join(directory,'out'),'w')
        err = open(os.path.join(directory,'err'),'w')
        def do():
            process = Popen(command,stdout=out,stdin=open('/dev/null'),stderr=err)
            rc=  process.wait()
            open(os.path.join(directory,'return_code')).write(str(rc))
        x=Process(None,do)
        x.start()
        open(os.path.join(directory,'time'),'w').write(str(time()))
        open(os.path.join(directory,'pid'),'w').write(str(x.pid))
        os.symlink(directory,os.path.join(self.tmp_dir,str(x.pid)))
        return x.pid

    @classmethod
    @ValidateIf
    def validate_resource_id(self,rid):
        return rid.isdigit()

    @classmethod
    def find(cls,pid):
        if not os.path.isdir(os.path.join(cls.tmp_dir,pid)):
            return None
        try:
            rc = int(open(os.path.join(cls.tmp_dir,pid,'return_code')).read())
        except IOError:
            rc = None
        return cls(pid,return_code=rc)

    def serialize(self):
        return {'rid':self.rid,
                'status': self.return_code and 'finished' or 'running',
                'return_code':self.return_code}

    @classmethod
    def find_all(self):
        pass

    @action
    def kill(self):
        pass

class UnixAccountHandler(object):
    """Gestionnaire des comptes UNIX """
    __metaclass__ = MetaHandler
    table_pwd = { 'name' : 'login', 'gid': 'gid', 'gecos':'comment' ,'shell':'shell','dir':'home'}

    name = Value('Login')
    gid = Value('Groupe ID')
    gecos = Value('Commentaire')
    dir = Value('Répertoire personnel')
    shell = Value('Shell de login')

    @classmethod
    def validate_resource_id(cls,r_id):
        """ UID de l'utilisateur"""
        try:
            return int(r_id)
        except ValueError:
            raise ValidationError,''

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

class APIUserHandler(object):
    """Gestionnaire des utilisateurs de l'API"""
    __metaclass__ = MetaHandler

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

    def __init__(self,client):
        self.client = client

    def serialize(self):
        return { 'rid':self.client.pk,'secret':self.client.value }

class InitdHandler(object):
    """ Gestionnaire des scripts init.d """
    __metaclass__ = MetaHandler

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
