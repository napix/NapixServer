#!/usr/bin/env python
# -*- coding: utf-8 -*-

import operator
import os

from pwd import getpwall,getpwuid
from napixd.exceptions import ValidationError,HTTP400,HTTP500,HTTPRC
from napixd.utils import run_command_or_fail,run_command,ValidateIf

from piston.utils import rc

from handler import MetaHandler,value,action,registry

class NAPIXAPI(object):
    """Service d'introspection de API"""
    url = 'napix'
    __metaclass__ = MetaHandler

    doc = value()
    fields = value()
    collection_methods = value()
    resource_methods = value()
    actions =value()

    @classmethod
    def find_all(cls):
        return registry.keys()

    @classmethod
    def find(cls,rid):
        try:
            handler = registry[rid]
        except KeyError:
            return None
        return cls(rid,
                doc = handler.__doc__,
                fields=handler.fields,
                collection_methods=handler.collection_methods,
                resource_methods = handler.resource_methods,
                actions=handler.actions)

class UnixAccountHandler(object):
    """Gestionnaire des comptes UNIX """
    __metaclass__ = MetaHandler
    table_pwd = { 'name' : 'login', 'gid': 'gid', 'gecos':'comment' ,'shell':'shell','dir':'home'}

    name = value()
    gid = value()
    gecos = value()
    dir = value()
    shell = value()

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
        try:
            login = values.pop('name')
        except KeyError:
            raise HTTP400,'<name> parameter required'
        for f,x in values.items():
            command.append('--'+self.table_pwd[f])
            command.append(x)
        command.append(login)
        code =  run_command(command)
        if code == 0:
            raise HTTPRC, rc.CREATED
        if code == 9:
            raise HTTPRC, rc.DUPLICATE_ENTRY
        raise HTTP500

    def modify(self,values):
        command = ['/usr/sbin/usermod']
        for f,x in values.items() :
            command.append('--'+self.table_pwd[f])
            command.append(x)
        command.append(self.name)
        run_command_or_fail(command)
        return rc.ALL_OK

    def remove(self,resource):
        run_command_or_fail(['/usr/sbin/userdel',resource['name']])
        return rc.DELETED

class InitdHandler(object):
    """ Gestionnaire des scripts init.d """
    __metaclass__ = MetaHandler

    path = '/etc/init.d'
    state = value()

    @property
    def script(self):
         return os.path.join(self.path,self.rid)

    def modify(self,values):
        if 'state' not in values:
            return HTTP400('<state> parameter required')
        status = values['state'] == 'off' and 'stop' or 'start'
        run_command_or_fail([self.script,status])
        return rc.ALL_OK

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
        run_command([self.script,'restart'])

