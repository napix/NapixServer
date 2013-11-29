#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Adapter(object):
    """
    A base class for the adapters.

    Each server must implements its own adapter sub-class.
    """
    def __init__(self, options):
        self.port = options.pop('port', 8000)
        self.host = options.pop('host', 'localhost')
        self.quiet = options.pop('quiet', False)
        self.options = options

    def run(self, handler):
        raise NotImplementedError()
