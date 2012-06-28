#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
from cStringIO import StringIO

class Response( object ):
    def __init__( self, headers=None, body=None):
        self.headers = headers or {}
        self._body = StringIO()

    def set_header(self, header, content):
        self.headers[header] = content

    def write(self, content):
        self._body.write(content)

    def read(self, size=-1):
        return self._body.read(size)

    def seek(self, offset, whence=0):
        return self._body.seek( offset, whence)

    def is_empty(self):
        self._body.seek(0, os.SEEK_END)
        return self._body.tell() == 0
