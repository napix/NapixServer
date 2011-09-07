#!/usr/bin/env python
# -*- coding: utf-8 -*-

from executor import executor

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

    def find_all(self):
        return executor.manager.keys()

    def get(self):
        return {'rid':self.rid,
                'command':self.process.request.command,
                'arguments':self.process.request.arguments,
                'status': self.process.returncode is None and 'running' or 'finished',
                'returncode':self.process.returncode,
                'stderr' : self.process.stderr.getvalue(),
                'stdout': self.process.stdout.getvalue()
                }

    def delete(self):
        self.process.kill()
        return 'ok'

