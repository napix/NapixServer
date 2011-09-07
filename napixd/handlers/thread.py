#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.handler import Collection,Resource,IntIdMixin
from threadator import thread_manager
from executor import executor

class ThreadManager(IntIdMixin,Collection):
    """Gestionnaire des taches asynchrones"""

    def find_all(self):
        return thread_manager.keys()

    def find(cls,rid):
        try:
            return Thread(thread_manager[rid])
        except KeyError:
            return None

class Thread(Resource):
    def __init__(self,thread):
        self.thread = thread

    def get(self):
        self.spawned_process = executor.children_of(self.thread.ident)
        return {
                'rid':self.thread.ident,
                'status':self.thread.status,
                'execution_state':self.thread.execution_state,
                'start_time':self.thread.start_time,
                }

