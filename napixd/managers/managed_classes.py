#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ManagedClass(object):

    """
    A managed class of a :class:`napixd.managers.base.Manager`.

    It contains a Promise to a Manager object by its Python path. The promise
    will be resolved with the final class by calling :meth:`resolve`
    """

    def __init__(self, manager_class, name='', extractor=None):
        if isinstance(manager_class, basestring):
            self.path = manager_class
            self.manager_class = None
        else:
            self.path = '%s.%s' % (
                manager_class.__module__, manager_class.__name__)
            self.manager_class = manager_class

        if extractor:
            self.extractor = extractor
        self.name = name

    def __repr__(self):
        return '<ManagedClass{resolved} {path}>'.format(
            path=self.path,
            resolved=' resolved' if self.is_resolved() else '')

    def is_resolved(self):
        """
        Returns `True` if the :meth:`resolve` has be called.
        """
        return self.manager_class is not None

    def resolve(self, cls):
        """
        Set the Manager class.
        """
        self.manager_class = cls

    def get_name(self):
        """
        Returns the name of the managed class.

        It raises a :exc:`ValueError` if the class is not
        :meth:`resolved<is_resolved>` yet.
        """
        if self.manager_class is None:
            raise ValueError('Managed class is not yet resolved')
        return self.name or self.manager_class.get_name()

    def extractor(self, parent):
        """
        Extract the resource from the parent.
        """
        return parent

    def __eq__(self, other):
        return isinstance(other, ManagedClass) and self.path == other.path
