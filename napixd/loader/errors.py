#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exceptions raised by the :class:`napixd.loader.importers.Importer`.

Thoses exceptions should not be raised out of the :mod:`napixd.loader` package,
but converted to :class:`napixd.loader.imports.ManagerError`.
"""


class NapixImportError(Exception):
    """
    Base Exception of loading errors.
    """
    pass

    def contains(self, manager):
        """
        Return if the *manager* is impacted by this error.
        """
        raise NotImplementedError()


class ModuleImportError(NapixImportError):
    """
    An error when importing a module.
    All manager inside this module are unavailable.
    """

    def __init__(self, module, cause):
        super(ModuleImportError, self).__init__(module, cause)
        self.module = module
        self.cause = cause

    def contains(self, manager):
        return self.module == manager.__module__


class ManagerImportError(NapixImportError):
    """
    An error when importing a manager.

    This manager is the only one impacted.
    """

    def __init__(self, module, manager, cause):
        super(ManagerImportError, self).__init__(module, manager, cause)
        self.module = module
        self.manager = manager
        self.cause = cause

    def contains(self, manager):
        return (self.module == manager.__module__ and
                self.manager == manager.__name__)
