#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
import traceback
import functools
import json
import logging

import bottle

import napixd

class ExceptionsCatcher(object):
    name = 'exceptions_catcher'
    api = 2
    logger = logging.getLogger('Napix.Errors')

    def __init__(self, show_errors=False, pprint=False):
        self.show_errors = show_errors
        self.napix_path = os.path.dirname( napixd.__file__)
        self.pprint = 4 if pprint else None

    def apply(self,callback,route):
        """
        This plugin run the view and catch the exception that are not HTTPResponse.
        The HTTPResponse are legit response, sent to the ConversationPlugin, the rest are errors.
        For this error, it send a dict containing the file, line and details of the exception
        """
        @functools.wraps(callback)
        def inner_exception_catcher(*args,**kwargs):
            try:
                return callback(*args,**kwargs) #Exception
            except bottle.HTTPResponse, e:
                return e
            except Exception,e:
                method = bottle.request.method
                path = bottle.request.path
                a, b, last_traceback = sys.exc_info()
                filename, lineno, function_name, text = traceback.extract_tb(last_traceback)[-1]
                if self.show_errors:
                    traceback.print_exc()
                all_tb = [ dict( zip( ('filename', 'line', 'in', 'call'), x))
                        for x in traceback.extract_tb( last_traceback ) ]
                extern_tb = [ x for x in all_tb
                        if not x['filename'].startswith(self.napix_path) ]
                self.logger.error('%s on %s failed with %s (%s)',  method, path,
                        e.__class__.__name__, str(e) )
                res = {
                        'request' : {
                            'method' : method,
                            'path' : path
                            },
                        'error_text': str(e),
                        'error_class': e.__class__.__name__,
                        'filename': filename,
                        'line': lineno,
                        'traceback' : extern_tb or all_tb,
                        }
                return bottle.HTTPResponse(
                        json.dumps(res, indent=self.pprint),
                        status=500,
                        content_type='application/json')
        return inner_exception_catcher

