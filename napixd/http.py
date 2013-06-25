#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
from cStringIO import StringIO

class Response( object ):
    """
    HTTP response object used for custom HTTP responses.

    This class implements the :class:`file` interface for its body,
    and has :meth:`set_header` for the HTTP headers.

    It is meant to be used with :mod:`napixd.manager.views` and
    be given to methods like :meth:`json.dump`, :meth:`PIL.Image.save` or :class:`reportlab.platypus.SimpleDocTemplate`.

    .. attribute:: headers

        A dict of the HTTP headers set.

    """
    def __init__( self, headers=None, body=None):
        self.headers = headers or {}
        self._body = StringIO()

    def set_header(self, header, content):
        """
        Set the HTTP header *header* to *content*
        """
        self.headers[header] = content

    def write(self, content):
        """
        Write content in the buffer
        """
        self._body.write(content)

    def read(self, size=-1):
        """
        Read up to *size* byte from the buffer.
        """
        return self._body.read(size)

    def seek(self, offset, whence=0):
        return self._body.seek( offset, whence)

    def is_empty(self):
        """
        Returns if the buffer is empty
        """
        self._body.seek(0, os.SEEK_END)
        return self._body.tell() == 0
