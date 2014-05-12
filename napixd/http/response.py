#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import httplib
from cStringIO import StringIO

from napixd.http.headers import HeadersDict

__all__ = [
    'Response',
    'HTTPResponse',
    'HTTPError',
    'HTTP403',
    'HTTP404',
    'HTTP405',
]

responses = dict(httplib.responses)
responses.update({
    429: 'Too Many Requests',
})


class Response(object):
    """
    HTTP response object used for custom HTTP responses.

    This class implements the :class:`file` interface for its body, and has
    :meth:`set_header` for the HTTP headers.

    It is meant to be used with :mod:`napixd.managers.views` and be given to
    methods like :meth:`json.dump`, :meth:`PIL.Image.save` or
    :class:`reportlab.platypus.SimpleDocTemplate`.

    .. attribute:: headers

        A dict of the HTTP headers set.

    """

    def __init__(self, headers=None):
        self.headers = HeadersDict(headers or {})
        self._body = StringIO()
        self._length = 0

    @property
    def size(self):
        return self._length

    def set_header(self, header, content):
        """
        Set the HTTP header *header* to *content*
        """
        self.headers[header] = content

    def write(self, content):
        """
        Write content in the buffer
        """
        if isinstance(content, unicode):
            content = content.encode('utf-8')

        self._length += len(content)
        self._body.write(content)

    def read(self, size=-1):
        """
        Read up to *size* byte from the buffer.
        """
        return self._body.read(size)

    def seek(self, offset, whence=0):
        return self._body.seek(offset, whence)

    def is_empty(self):
        """
        Returns if the buffer is empty
        """
        self._body.seek(0, os.SEEK_END)
        return self._body.tell() == 0


class HTTPResponse(object):
    """
    HTTPResponse([[status,] headers,] body)

    A HTTP response.

    *status* is the status of the response, by default 200.
    *headers* is a mapping of HTTP headers.
    *body* is the content of the response.

    If body is a :class:`HTTPResponse` or a :class:`HTTPError`, the headers are
    merged with the given headers and the body of the original object is used.
    If the status is not specified, the status of the response is used.
    """
    def __init__(self, *args):
        length = len(args)
        if length == 0:
            status, headers, body = 200, {}, None
        elif length == 1:
            body, = args
            status, headers = 200, {}
        elif length == 2:
            headers, body = args
            status = 200
        elif length == 3:
            status, headers, body = args
        else:
            raise TypeError('HTTPResponse takes up to 3 arguments')

        if isinstance(body, Response):
            self._headers = HeadersDict(body.headers)
            self._headers.update(headers)
            self._headers.setdefault('Content-Length', body.size)
            body.seek(0)
            self._body = body
        elif isinstance(body, (HTTPResponse, HTTPError)):
            self._headers = HeadersDict(body.headers)
            self._headers.update(headers)
            self._body = body.body
            if length != 3:
                status = body.status
        else:
            self._body = body
            self._headers = HeadersDict(headers)

        self.status = status

    def __repr__(self):
        ret = [self.status_line]
        ret.extend('{0}: {1}'.format(*items) for items in self.headers.items())
        ret.append('')
        ret.append(str(self.body))
        return '\n'.join(ret)

    @property
    def status_line(self):
        """The HTTP Status line as expected by start_response"""
        reason = responses.get(self.status, 'Unknown')
        return '{0} {1}'.format(self.status, reason)

    @property
    def headers(self):
        """The headers of the response"""
        return self._headers

    @property
    def body(self):
        """The body of the response"""
        return self._body

    def __eq__(self, other):
        return (isinstance(other, HTTPResponse) and
                self.status == other.status and
                self.headers == other.headers and
                self.body == other.body)


class HTTPError(BaseException):
    """
    A error that occurred and is transcribed as a HTTP response.

    *status* is the status response.

    *body* is a line of text or a more complex object.
    """
    def __init__(self, status, body='', **headers):
        self.status = status
        self.body = body
        self.headers = HeadersDict(headers)
        super(HTTPError, self).__init__()


class HTTP403(HTTPError):
    """
    403 Forbidden
    """
    def __init__(self):
        super(HTTP403, self).__init__(403, 'The access to this page is forbidden')


class HTTP404(HTTPError):
    """
    404 Not found
    """
    def __init__(self, text=''):
        super(HTTP404, self).__init__(404, text or 'ERROR 404: The requested page does not exists')


class HTTP405(HTTPError):
    """
    405 Not allowed HTTP Error.

    It takes a list of allowed HTTP methods.
    """
    def __init__(self, allowed):
        super(HTTP405, self).__init__(405,
                                      'ERROR 405: The method is not allowed',
                                      allow=','.join(allowed)
                                      )
