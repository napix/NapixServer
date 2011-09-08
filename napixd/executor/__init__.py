#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
from .base import Executor
from .manager import ExecManager

__all__ = ['executor','popen','run_command','run_command_or_fail','exec_manager']

executor = Executor()

popen = executor.create_job

def run_command(command):
    """Run a command and return the return code"""
    return executor.create_job(command,discard_output=True).wait()
def run_command_or_fail(command):
    """Run a command and throw an exception if the return code isn't 0"""
    code = run_command(command)
    if code != 0:
        raise subprocess.CalledProcessException,'Oops command <%s> returned %i'%(subprocess.list2cmdline(command),code)

exec_manager = ExecManager(executor)
