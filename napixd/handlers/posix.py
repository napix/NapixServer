#!/usr/bin/env python
# -*- coding: utf-8 -*-


from grp import getgrall,getgrgid
from pwd import getpwuid,getpwall,getpwnam
import operator
from napixd.handler import Collection,Resource,IntIdMixin,Value
from napixd.utils import run_command_or_fail,run_command


class UnixGroupManager(IntIdMixin,Collection):
    def find_all(self):
        return map(operator.itemgetter(2),getgrall())

    def find(cls,rid):
        try:
            group = getgrgid(rid)
            inst = UnixGroup(rid,name=group.gr_name)
            inst.members = group.gr_mem
            return inst
        except KeyError:
            return None

class UnixGroup(Resource):
    name = Value('Group name')

    def modify(self,values):
        new_name = values['name']
        command = ['groupmod','-n',new_name,self.name]
        run_command_or_fail(command)

class UnixAccount(Resource):
    table_pwd = { 'name' : 'login', 'gid': 'gid', 'gecos':'comment' ,'shell':'shell','dir':'home'}

    name = Value('Login')
    gid = Value('Groupe ID')
    gecos = Value('Commentaire')
    dir = Value('Répertoire personnel')
    shell = Value('Shell de login')

    def modify(self,values):
        command = ['/usr/sbin/usermod']
        for f,x in values.items() :
            command.append('--'+self.table_pwd[f])
            command.append(x)
        command.append(self.name)
        run_command_or_fail(command)

    def remove(self,resource):
        run_command_or_fail(['/usr/sbin/userdel',resource['name']])

class UnixAccountManager(IntIdMixin,Collection):
    """Gestionnaire des comptes UNIX """
    resource_class = UnixAccount

    def find(cls,uid):
        try:
            x= getpwuid(uid)
        except KeyError:
            return None
        self = UnixAccount(uid)
        for i in cls._meta.fields:
            setattr(self,i,getattr(x,'pw_'+i))
        return self

    def find_all(self):
        return [x.pw_uid for x in getpwall()]

    def create(cls,values):
        command = ['/usr/sbin/useradd']
        login = values.pop('name')
        for f,x in values.items():
            command.append('--'+UnixAccount.table_pwd[f])
            command.append(x)
        command.append(login)
        code =  run_command(command)
        if code == 0:
             return getpwnam(login).pw_uid
