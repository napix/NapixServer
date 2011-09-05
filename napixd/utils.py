#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import logging
import subprocess



from executor import executor

from napixd.exceptions import ValidationError

__all__ = ['run_command_or_fail','run_command','ValidateIf']

def run_command_or_fail(command):
    """Run a command and throw an exception if the return code isn't 0"""
    code = run_command(command)
    if code != 0:
        raise Exception,'Oops command <%s> returned %i'%(subprocess.list2cmdline(command),code)

def run_command(command):
    """Run a command and return the return code"""
    return executor.create_job(command,discard_output=True,managed=False).wait()

def ValidateIf(fn):
    @functools.wraps(fn)
    def inner(self,r_id):
        if not fn(self,r_id):
            raise ValidationError,''
        return r_id
    return inner
