#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools

def view(format_):
    def inner(fn):
        fn._napix_view = format_
        return fn
    return inner

def content_type(content_type):
    def inner(fn):
        @functools.wraps(fn)
        def wrapper(self, id_, resource, response):
            response.set_header('Content-Type', content_type)
            return fn(self, id_, resource, response)
        return wrapper
    return inner
