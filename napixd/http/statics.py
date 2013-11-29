#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A static file server.
"""

import os
import time
import mimetypes
import email.utils

from napixd.http.response import HTTP403, HTTP404, HTTPResponse

__all__ = ['StaticFile', 'StaticFiles']


class StaticFiles(object):
    """
    A static file server callback.

    The *root* is the path containing all the files served.
    All files must served must be inside this path.
    """
    def __init__(self, root):
        self.root = os.path.join(os.path.abspath(root), '')

    def __call__(self, request, path):
        path = os.path.abspath(os.path.join(self.root, path))
        if not path.startswith(self.root):
            raise HTTP403
        return StaticFile(request, path)


def parse_date(ims):
    """ Parse rfc1123, rfc850 and asctime timestamps and return UTC epoch. """
    try:
        ts = email.utils.parsedate_tz(ims)
        return time.mktime(ts[:8] + (0,)) - (ts[9] or 0) - time.timezone
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


class StaticFile(HTTPResponse):
    """
    A response to a static file request.

    The *request* is the original request.
    The *filename* is the absolute path to the file.
    """
    def __init__(self, request, filename):
        self.request = request
        self.filename = filename
        try:
            self.stats = os.stat(filename)
        except OSError:
            raise HTTP404()

        if self.is_in_cache():
            status = 304
            headers = {'Date': time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())}
            body = None
        else:
            status = 200
            content_type, encoding = mimetypes.guess_type(self.filename)

            if content_type is None:
                content_type = 'application/octet-stream'

            if content_type.startswith('text/'):
                content_type += '; charset=utf-8'

            headers = {
                'Content-Type': content_type,
                'Content-length': self.content_length,
                'Last-Modified': self.last_modified,
            }
            if encoding:
                headers['Content-Encoding'] = encoding
            body = '' if request.method == 'HEAD' else self.open_file()

        super(StaticFile, self).__init__(status, headers, body)

    @property
    def last_modified(self):
        """The last modified time of the file"""
        return time.strftime('%a, %d %b %Y %H:%M:%S GMT',
                             time.gmtime(self.stats.st_mtime))

    @property
    def content_length(self):
        """The file size"""
        return self.stats.st_size

    def is_in_cache(self):
        """Return True if the file is in the cache of the client"""
        ims = self.request.headers.get('HTTP_IF_MODIFIED_SINCE')
        if ims:
            ims = parse_date(ims.split(";")[0].strip())
        return ims is not None and ims >= self.stats.st_mtime

    def open_file(self):
        """
        Opens the file and return a handle.
        """
        try:
            return open(self.filename, 'rb')
        except IOError:
            raise HTTP404('No such file or directory {0}'.format(self.request.path))
