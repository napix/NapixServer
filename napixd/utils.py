#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import logging
import subprocess
from napixd.exceptions import HTTP500,ValidationError

logger = logging.getLogger('commands')

def run_command_or_fail(command):
    code = run_command(command)
    if code != 0:
        raise HTTP500,'Oops command returned '+code

def run_command(command):
    logger.info('Running '+' '.join(command))
    shell = subprocess.Popen(command,stderr=open('/dev/null'),stdout=open('/dev/null'))
    return shell.wait()

def ValidateIf(fn):
    @functools.wraps(fn)
    def inner(self,r_id):
        if not fn(self,r_id):
            raise ValidationError,''
        return r_id
    return inner
