#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import sys

from napixd.conf import Conf, BaseConf, EmptyConf
from napixd.managers.base import Manager

from napixd.loader.errors import (
    ModuleImportError, ManagerImportError, NapixImportError)
from napixd.loader.imports import ManagerImport

logger = logging.getLogger('Napix.loader.importers')

import_fn = __import__


class Importer(object):
    """
    The base class of the manager importers.

    Subclasse must define a :meth:`load` method that will use
    :meth:`import_manager` and :meth:`import_module` to find on its location.

    .. attribute:: timestamp

        The last check for this object

    .. attribute:: raise_on_first_import

        Set to :data:`True` if the fails on the first import
        should raise errors.
        Else the errors are silently ignored.

        Errors thrown will prevent the napixd server from starting.
    """

    def __init__(self, raise_on_first_import=True):
        self.timestamp = 0
        self.errors = []
        self.raise_on_first_import = raise_on_first_import

    @property
    def should_raise(self):
        return self.raise_on_first_import and self.timestamp == 0

    def get_paths(self):
        """
        Return the paths watched by this manager.
        """
        return []

    def set_timestamp(self, timestamp):
        """
        Set :attr:`timestamp` to now.
        """
        self.timestamp = timestamp

    def load(self):
        """
        Do the loading.

        It must return a tuple of two iterables, *managers* and *errors*
        *managers* is an iterable of :class:`~napixd.managers.base.Manager`
        sub-classes.
        *errors* are the errors that happended during the loading.
        """
        raise NotImplementedError

    def first_import(self, module_path):
        """
        Import the module for the first time.
        """
        # first module import
        logger.debug('import %s', module_path)
        import_fn(module_path)
        return sys.modules[module_path]

    def has_been_modified(self, module_file, module_name):
        """
        Returns `True` if the *module_file* has been modified
        since the last check.
        """
        try:
            last_modif = os.stat(module_file).st_mtime
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('File %s last modified at %s %s %s',
                             module_name, last_modif,
                             self.timestamp,
                             'reload' if last_modif > self.timestamp else '')
        except OSError as e:
            logger.error('Failed to get file %s, %s', module_name, e)
            raise ModuleImportError(module_name, 'Module does not exists anymore')

        return last_modif > self.timestamp

    def reload(self, module_path):
        """
        Try to reload the module if it was modified since the last time.
        """
        module = sys.modules[module_path]
        if module.__file__.endswith('pyc'):
            module_file = module.__file__[:-1]
        else:
            module_file = module.__file__

        if self.has_been_modified(module_file, module_path):
            # modified since last access
            logger.debug('Reloading module %s', module_path)
            reload(module)
        return module

    def import_module(self, module_path):
        """
        imports a module.
        """
        if not isinstance(module_path, basestring):
            raise TypeError('module_path is a string')

        try:
            if module_path not in sys.modules or self.timestamp == 0:
                return self.first_import(module_path)
            else:
                return self.reload(module_path)
        except NapixImportError:
            raise
        except Exception as e:
            logger.error('Failed to import %s, %s', module_path, e)
            raise ModuleImportError(module_path, e)

    def import_manager(self, manager_path, reference=None):
        """
        Imports a manager.

        *manager_path* is a :class:`~napixd.managers.base.Manager`,
        a full path to a Manager subclass or a name in the *reference* module.

        *reference* is used only when *manager_path* is just a name.
        """
        logger.debug('Import Manager %s', manager_path)
        if isinstance(manager_path, type) and issubclass(manager_path, Manager):
            module_path = manager_path.__module__
            manager_name = manager_path.__name__
        else:
            module_path, x, manager_name = manager_path.rpartition('.')

        if not module_path:
            if reference:
                module_path = reference.__module__
            else:
                raise ValueError('manager_path must contains the module name')

        module = self.import_module(module_path)
        try:
            return getattr(module, manager_name)
        except AttributeError:
            logger.error('Module %s does not contain %s', module_path, manager_name)
            raise ManagerImportError(module_path, manager_name,
                                     'Module {0} has no {1}'.format(module_path, manager_name))

    def setup(self, manager):
        """
        Loads the managed classes of a manager


        It checks that all the manager and sub-managers have defined a resource_fields dict.
        """
        return self._setup(manager, set())

    def _setup(self, manager, _already_loaded):
        if manager in _already_loaded:
            logger.info('Circular manager detected: %s', manager.get_name())
            return manager
        _already_loaded.add(manager)

        if not manager._resource_fields:
            raise ManagerImportError(manager.__module__, manager,
                                     'This manager has no resource_fields')

        managed_classes = manager.get_managed_classes()
        if managed_classes:
            importer = RelatedImporter(manager, raise_on_first_import=self.should_raise)
            managed_classes, errors = importer.load(managed_classes)
            if errors:
                raise ManagerImportError(
                    manager.__module__, manager, errors[0])
            for managed_class in managed_classes:
                self._setup(managed_class, _already_loaded)

        return manager


class FixedImporter(Importer):

    """
    Imports a list of managers.

    It takes a *managers* dict of the service name mapping to either a tuple
    (:class:`Manager subclass<napixd.managers.base.Manager>`, config)
    or just the Manager subclass.

    >>> FixedImporter({'this': ('ThisManager', { 'a' : 1 })})
    >>> FixedImporter({'that': 'ThatManager'})
    """

    def __init__(self, managers):
        super(FixedImporter, self).__init__()
        self.managers = managers

    def load(self):
        managers, errors = [], []
        for alias, spec in self.managers.items():
            try:
                manager, conf = spec
            except ValueError:
                manager, conf = spec, EmptyConf()
            else:
                if not isinstance(conf, BaseConf):
                    conf = Conf(conf)

            logger.info('Import fixed %s', manager)
            try:
                manager = self.import_manager(manager)
                manager = self.setup(manager)
            except NapixImportError as e:
                if self.should_raise:
                    raise
                errors.append(e)
            else:
                managers.append(ManagerImport(manager, alias, conf))
        return managers, errors


class ConfImporter(Importer):

    """
    Imports the manager as specified in the config file.:

    It refers to the :ref:`conf.napix.managers` to find the managers name.

    The config of each manager is found in the
    :mod:`default configuration<napixd.conf>` of Napix.
    """

    def __init__(self, managers, conf):
        super(ConfImporter, self).__init__()
        self.managers = managers
        self.conf = conf

    def get_paths(self):
        for manager_path in self.managers.values():
            module = sys.modules.get(manager_path.rsplit('.', 1)[0])
            if module:
                yield os.path.dirname(module.__file__)

    def load(self):
        """
        Load the managers with the conf
        return a list of Manager subclasses
        """
        managers, errors = [], []
        for alias, manager_path in self.managers.items():
            try:
                manager = self.import_manager(manager_path)
                logger.info('load %s from conf', manager_path)
                config = self.conf.get('Manager ' + alias)
                manager = self.setup(manager)
            except NapixImportError as e:
                if self.should_raise:
                    raise
                errors.append(e)
            else:
                import_ = ManagerImport(manager, alias, config)
                managers.append(import_)
        return managers, errors


class RelatedImporter(Importer):
    """
    Imports the managed classes.

    The *reference* parameter is a manager class.
    The submanager classes are searched in the same module than the *reference*
    class if the path does not contains ``.``
    """

    def __init__(self, reference, raise_on_first_import=False):
        super(RelatedImporter, self).__init__(raise_on_first_import=raise_on_first_import)
        self.reference = reference

    def load(self, classes):
        """
        Loads the the managed *classes* of :attr:`reference`
        """
        logger.debug('loading related classes')
        managed_classes = []
        for cls in classes:
            if not cls.is_resolved():
                try:
                    managed_class = self.import_manager(
                        cls.path, reference=self.reference)
                    cls.resolve(managed_class)
                except NapixImportError as e:
                    return [], [e]
            managed_classes.append(cls.manager_class)
        return managed_classes, []
