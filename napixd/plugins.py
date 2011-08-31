#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from bottle import request

class ConversationPlugin(object):
    name = "conversation_plugin"
    api = 2
    def apply(self,callback,route):
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
