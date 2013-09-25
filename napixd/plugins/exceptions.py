#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:mod:`bottle` plugin for the exceptions
"""

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
    """
    Catch the exception raised by the decorated function.

    When an exception is caught, the traceback, the exception value
    and the details of the error are extracted and returned in a :class:`dict`.

    If *pprint* is True, the produced JSON will be indented.
    If *show_errors* is True, the exceptions are printed on the console.
    """
    name = 'exceptions_catcher'
    api = 2
    logger = logging.getLogger('Napix.Errors')

    def __init__(self, show_errors=False, pprint=False):
        self.show_errors = show_errors
        self.napix_path = os.path.dirname(napixd.__file__)
        self.pprint = 4 if pprint else None

    def extract_error(self, error):
        """
        Extract a :class:`dict` from an exception.

        It adds the keys ``request`` containing the details of the HTTP request
        causing the exception.
        """
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
        """
        When the error is a :exc:`napix.exceptions.HTTPError`,
        it adds the keys ``remote_call`` with the remote request description
        and ``remote_error`` with the detail of the error.
        """
        return {
            'remote_call': unicode(error.request),
            'remote_error': error.remote_error or str(error)
        }

    def traceback_info(self, last_traceback):
        """
        Extracts the informations from the traceback.

        Add the keys ``filename`` and ``line`` pointing to the root
        of the exception.
        Also adds the key ``traceback`` containing a dump of the traceback
        as a :class:`list`.
        """
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
        """
        Adds the key ``error_text`` with the string value of the exception and
        the key ``error_class`` with the class name of the exception.
        """
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
