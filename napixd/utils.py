#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import logging
import subprocess
from napixd.exceptions import ValidationError
from bottle import request

command_logger = logging.getLogger('commands')
request_logger = logging.getLogger('request')

def run_command_or_fail(command):
    code = run_command(command)
    if code != 0:
        raise Exception,'Oops command <%s> returned %i'%(subprocess.list2cmdline(command),code)

def run_command(command):
    return request.create_job(command,discard_output=True,managed=False).wait()

def ValidateIf(fn):
    @functools.wraps(fn)
    def inner(self,r_id):
        if not fn(self,r_id):
            raise ValidationError,''
        return r_id
    return inner
