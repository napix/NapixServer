#!/usr/bin/env python
# -*- coding: utf-8 -*-


from django.core.exceptions import ValidationError,PermissionDenied

class HTTPException(Exception):
    status = 200
class HTTP400(HTTPException):
    status = 400
class HTTP404(HTTPException):
    status = 404
class HTTP405(HTTPException):
    status = 405
class HTTP500(HTTPException):
    status = 500

class HTTPRC(Exception):
    def __init__(self,rc):
        self.rc=rc

class HTTPWithContent(Exception):
    status = 200
    def __init__(self,content,status=None):
        self.content = content
        self.status = status or self.__class__.status

class HTTPRedirect(HTTPWithContent):
    status = 301
    def __init__(self,url,content):
        HTTPWithContent.__init__(self,content)
        self.url = url

class HTTPForbidden(HTTPWithContent):
    status = 403
