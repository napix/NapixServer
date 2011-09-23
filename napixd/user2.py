#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.resources.by_collection import SimpleCollection
from napixd.exceptions import ValidationError,NotFound
from napixd.executor import executor
import pwd

class User(SimpleCollection):
    fields = ['uid','username','shell']

    def check_id(self,id_):
        try:
            return int(id_)
        except (ValueError,TypeError):
            raise ValidationError

    def create(self,data):
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

    def list(self,filters):
        return [x.pw_uid for x in pwd.getpwall()]

    def get_child(self,id_):
        try:
            user = pwd.getpwuid(id_)
        except KeyError:
            raise NotFound
        return {'uid':user.pw_uid,'username':user.pw_name,'shell':user.pw_shell}

    def delete(self,username):
        command = ['/usr/bin/userdel']
        command.append(username)
        rc = executor.create_job(command).wait()

