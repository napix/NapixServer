#!/usr/bin/env python
# -*- coding: utf-8 -*-

class ManagedClass(object):
    def __init__(self, manager_class, name='', extractor=None):
        self.manager_class = manager_class
        if extractor:
            self.extractor = extractor
        self.name = name

    def is_resolved(self):
        return not isinstance( self.manager_class, basestring)

    def resolve(self, cls):
        self.manager_class = cls

    def get_name( self):
        return self.name or self.manager_class.get_name()

    def extractor(self, parent):
        return parent

