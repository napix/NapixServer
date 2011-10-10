#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect

def action(fn):
    """
    Decorator to declare an action method inside a handler

    FIXME : c'est a dire ? :D
    Quoi que ca fait, etc etc.
    """
    param = inspect.getargspec(fn)
    args = param.args
    #self
    args.pop(0)
    #default values
    opt = param.defaults or []

    #mandatory params = param list - param that have default values
    len_mand = len(args) - len(opt)
    fn.mandatory = args[:len_mand]
    fn.optional = dict(zip(args[len_mand:],opt))
    fn._napix_action=True

    return fn
