#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time

from napixd.loader.importers import RelatedImporter
from napixd.loader.imports import ManagerError
from napixd.loader.errors import NapixImportError, ManagerImportError

__all__ = ('Loader', 'Load')

logger = logging.getLogger('Napix.loader')


class Load(object):
    """
    An object representing a collections of :class:`imports.ManagerImport`
    """
    __slots__ = ('old_managers', 'managers', 'new_managers', 'error_managers')

    def __init__(self, old_managers, managers, new_managers, error_managers):
        self.old_managers = old_managers
        self.managers = managers
        self.new_managers = new_managers
        self.error_managers = error_managers

import_fn = __import__
open = open


class Loader(object):
    """
    Finds and keeps track of the managers.

    The loader takes a list of :class:`importers.Importer` instances.
    Each time the loader runs a loading cycle,
    it calls the :meth:`importers.Importer.load` on each of them and gets
    the managers and errors.

    The managers set is compared to the previous and a :class:`Load`
    object is created with the new and the olds managers

    .. attribute:: managers

        The set of :class:`imports.ManagerImport` loaded.
    """

    def __init__(self, importers):
        self.importers = importers
        self.managers = set()
        self.errors = set()
        self.timestamp = 0

    def get_paths(self):
        """
        List the paths to watch with :mod:`napixd.reload`
        """
        paths = set()
        for importer in self.importers:
            paths.update(importer.get_paths())
        return paths

    def load(self):
        """
        Runs a loading cycle

        Returns a :class:`Load` instance with the variation
        that have happened since the last :meth:`load` call.
        """
        logger.info('Run a load at %s', self.timestamp)
        managers = set()
        import_errors = []

        for importer in self.importers:
            importer.set_timestamp(self.timestamp)
            imports, errors_ = importer.load()

            managers.update(imports)
            import_errors.extend(errors_)

        new_managers = managers.difference(self.managers)
        old_managers = self.managers.difference(managers)

        errors = set()
        for old in old_managers:
            for error in import_errors:
                if error.contains(old.manager):
                    errors.add(ManagerError(
                        old.manager, old.alias, error.cause))
                    break

        for previous_error in self.errors:
            for error in import_errors:
                if error.contains(previous_error.manager):
                    errors.add(ManagerError(previous_error.manager,
                                            previous_error.alias, error.cause))
                    break
            else:
                old_managers.add(previous_error)

        self.managers = managers
        self.errors = errors
        self.timestamp = time.time()
        return Load(old_managers, managers, new_managers, errors)
