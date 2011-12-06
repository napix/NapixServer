#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect

__all__ = ('action', )

def action(fn):
    """
    Decorator to declare an action method inside a handler

    """
    param = inspect.getargspec(fn)
    #ignore first two parameters: self and resource
    args = param.args[2:]
    #default values
    opt = param.defaults or []

    fn.all_parameters = set(args)
    #mandatory params = param list - param that have default values
    len_mand = len(args) - len(opt)
    fn.mandatory = args[:len_mand]
    fn.optional = dict(zip(args[len_mand:],opt))
    fn._napix_action=True

    fn.resource_fields = {}
    for param in fn.mandatory:
        fn.resource_fields[param] = { 'example' : '' , 'description' : '' }

    for param, default in fn.optional.items() :
        fn.resource_fields[param] = { 'example' : '' , 'description' : '' ,
                'optional': True }
    return fn

def parameter(name, **kw):
    def inner(fn):
        fn.resource_fields[name].update(kw)
        return fn
    return inner
