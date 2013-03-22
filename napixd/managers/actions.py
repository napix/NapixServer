#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Actions
=======

Action are arbitrary python function that can be called on a resource of a collection.
"""

import inspect

__all__ = ('action', 'parameter' )

def action(fn):
    """
    Decorates a python function that will be an action

    The action takes the resource as its first argument.

    The decorator automatically discovers the mandatory and optional arguments of the function
    and use them for documentation and template request generation.

    .. code-block:: python

        class RouterManager( Manager ):
            resource_fields = {
                    'ip' : {
                        'description' : 'IP of the target router'
                    }
                }
            ...
            @action
            def ping(self, router, tries=3):
                for x in tries:
                    if ping( router['ip']):
                        return 'Router responds'
                return 'Router Unreachable'
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
    """
    Allow to set one or several parameters on an action.

    .. code-block:: python

        @parameter( 'tries',  description = 'Number of times we try to ping' )
        @action
        def ping(self, router, tries=3):
            for x in tries:
                if ping( router['ip']):
                    return 'Router responds'
            return 'Router Unreachable'
    """
    def inner(fn):
        fn.resource_fields[name].update(kw)
        return fn
    return inner
