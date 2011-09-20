#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import json
from cStringIO import StringIO
from bottle import request,HTTPResponse

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
            buff = StringIO()
            json.dump(res,buff)
            return HTTPResponse(buff.getvalue(),
                    header=[('Content-Type', 'application/json')])
        return inner
