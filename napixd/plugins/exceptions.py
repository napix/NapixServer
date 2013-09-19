#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
import traceback
import functools
import json
import logging

import bottle
from napix.exceptions import HTTPError

import napixd


class ExceptionsCatcher(object):
    name = 'exceptions_catcher'
    api = 2
    logger = logging.getLogger('Napix.Errors')

    def __init__(self, show_errors=False, pprint=False):
        self.show_errors = show_errors
        self.napix_path = os.path.dirname(napixd.__file__)
        self.pprint = 4 if pprint else None

    def extract_error(self, error):
        a, b, last_traceback = sys.exc_info()
        method = bottle.request.method
        path = bottle.request.path
        self.logger.error('%s on %s failed with %s (%s)',
                          method, path, error.__class__.__name__, str(error))
        res = {
            'request': {
                'method': method,
                'path': path,
                'query': dict(bottle.request.GET),
            }
        }
        res.update(self.traceback_info(last_traceback))
        if isinstance(error, HTTPError):
            res.update(self.remote_exception(error))
        res.update(self.exception_details(error))
        return res

    def remote_exception(self, error):
        return {
            'remote_call': unicode(error.request),
            'remote_error': error.remote_error or str(error)
        }

    def traceback_info(self, last_traceback):
        all_tb = [dict(zip(('filename', 'line', 'in', 'call'), x))
                  for x in traceback.extract_tb(last_traceback)]
        extern_tb = [x for x in all_tb
                     if not x['filename'].startswith(self.napix_path)]
        filename, lineno, function_name, text = traceback.extract_tb(
            last_traceback)[-1]
        return {
            'traceback': extern_tb or all_tb,
            'filename': filename,
            'line': lineno,
        }

    def exception_details(self, error):
        return {
            'error_text': str(error),
            'error_class': error.__class__.__name__,
        }

    def apply(self, callback, route):
        """
        This plugin run the view and catch the exception that are not
        :class:`HTTPResponses<bottle.HTTPResponse>`.
        The HTTPResponse are legit response and are sent to the
        :class:`napixd.plugins.conversation.ConversationPlugin`,
        the rest are errors.
        """
        @functools.wraps(callback)
        def inner_exception_catcher(*args, **kwargs):
            try:
                return callback(*args, **kwargs)  # Exception
            except bottle.HTTPResponse, e:
                return e
            except Exception, e:
                res = self.extract_error(e)
                if self.show_errors:
                    traceback.print_exc()
                return bottle.HTTPResponse(
                    json.dumps(res, indent=self.pprint),
                    status=500,
                    content_type='application/json')
        return inner_exception_catcher
