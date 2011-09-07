#!/usr/bin/env python
# -*- coding: utf-8 -*-


from napixd.handler import Collection,Resource,action,Value
from napixd.utils import run_command_or_fail,ValidateIf,run_command
import os

class InitdManager(Collection):
    """ Gestionnaire des scripts init.d """


    def __init__(self,path=None):
        self.path = path or '/etc/init.d'

    def find(cls,rid):
        path = os.path.join(cls.path,rid)
        if not os.path.isfile(path):
            return None
        running = (run_command([path,'status']) == 0)
        instance = Initd(rid,state=running and 'on' or 'off')
        return instance

    def find_all(cls):
        return filter(lambda x:x[0]!='.',os.listdir(cls.path))

    @ValidateIf
    def validate_resource_id(self,name):
        """ nom du daemon """
        return not '/' in name

class Initd(Resource):
    state = Value('Etat')

    def modify(self,values):
        status = values['state'] == 'off' and 'stop' or 'start'
        run_command_or_fail([self.script,status])

    @property
    def script(self):
         return os.path.join(self.path,self.rid)

    @action
    def restart(self):
        """Restart the service"""
        run_command_or_fail([self.script,'restart'])
