#!/usr/bin/env python
# -*- coding: utf-8 -*-

class ManagedClass(object):
    def __init__(self, manager_class, name='', extractor=None):
        if isinstance(manager_class, basestring):
            self._managed_class_path = manager_class
            self.manager_class = None
        else:
            self._managed_class_path = '%s.%s' % ( manager_class.__module__, manager_class.__name__)
            self.manager_class = manager_class

        if extractor:
            self.extractor = extractor
        self.name = name

    def is_resolved(self):
        return self.manager_class is not None

    def resolve(self, cls):
        self.manager_class = cls

    def get_name( self):
        if self.manager_class is None:
            raise ValueError, 'Managed class is not yet resolved'
        return self.name or self.manager_class.get_name()

    def extractor(self, parent):
        return parent

    def __eq__(self, other):
        return ( isinstance(other, ManagedClass) and
                self._managed_class_path == other._managed_class_path)
