#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import json
from bottle import request

__all__ = ['ConversationPlugin']

class ConversationPlugin(object):
    """Plugin Bottle to convert
    from and to the python native objects to json
    """
    name = "conversation_plugin"
    api = 2
    def apply(self,callback,route):
        @functools.wraps(callback)
        def inner(*args,**kwargs):
            if 'CONTENT_TYPE' in request and request['CONTENT_TYPE'].startswith('application/json'):
                request.data = json.load(request.body)
            else:
                request.data = request.forms
            res = callback(*args,**kwargs)
            if hasattr(res,'serialize'):
                return res.serialize()
            return res
        return inner
