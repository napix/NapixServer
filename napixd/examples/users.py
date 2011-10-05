#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.resources.by_resource import SimpleResource
from napixd.exceptions import ValidationError,NotFound
from napixd.executor import executor
import pwd


"""
Example de module de gestion d'utilisateurs ecrit par la resource
"""


class User(object):
    fields = ['uid','username','shell']

    @classmethod
    def check_id(cls,id_):
        try:
            return int(id_)
        except (ValueError,TypeError):
            raise ValidationError

    @classmethod
    def create(cls,data):
        command = ['/usr/sbin/useradd']
        if 'uid' in data:
            command.append('-u')
            command.append(data['uid'])
        if 'shell' in data:
            command.append('-s')
            command.append(data['shell'])
        command.append(data['username'])
        rc = executor.create_job(command).wait()
        if rc == 0:
            return pwd.getpwnam(data['username']).pw_uid

    @classmethod
    def list(cls,filters):
        return [x.pw_uid for x in pwd.getpwall()]

    @classmethod
    def child(cls,id_):
        try:
            user = pwd.getpwuid(id_)
        except KeyError:
            raise NotFound
        return cls(user)

    def __init__(self,user):
        self.uid = user.pw_uid
        self.username = user.pw_name
        self.shell = user.pw_shell

    def delete(self):
        command = ['/usr/bin/userdel']
        command.append(self.username)
        rc = executor.create_job(command).wait()


class UserManager(SimpleResource):
    def __init__(self):
        super(UserManager,self).__init__(User)

