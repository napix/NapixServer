#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import imp
import logging
import os.path

from napixd.conf.json import ConfFactory as JSONConfFactory
from napixd.loader.importers import Importer
from napixd.loader.errors import (
    ModuleImportError, ManagerImportError, NapixImportError)
from napixd.loader.imports import ManagerImport
from napixd.managers import Manager
from napixd.conf import EmptyConf

try:
    from napixd.conf.dotconf import ConfFactory as DotconfConfFactory
except ImportError:
    DotconfConfFactory = None


__all__ = [
    'AutoImporter',
]


logger = logging.getLogger('Napix.loader.importers.auto')


class BaseAutoImporter(Importer):
    def __init__(self, path, raise_on_first_import=False):
        super(BaseAutoImporter, self).__init__(raise_on_first_import)
        self.path = path

    def load_module(self, module):
        """
        Explore a module and search for
        :class:`napixd.managers.base.Manager` subclasses.
        The method :meth:`~napixd.managers.base.Manager.detect` is called and
        if it returns False, the manager is ignored.

        The configuration is loaded from the docstring
        of the :meth:`~napixd.managers.base.Manager.configure` method.
        """

        managers, errors = [], []
        content = getattr(module, '__all__', False) or dir(module)
        for manager_name in content:
            try:
                obj = getattr(module, manager_name)
            except AttributeError as e:
                errors.append(ManagerImportError(
                    module.__name__, manager_name, e))
                continue

            if not isinstance(obj, type) or not issubclass(obj, Manager):
                continue

            try:
                detect = obj.detect()
            except Exception as e:
                logger.error('Error while running detect of manager %s.%s',
                             module.__name__, manager_name)
                errors.append(ManagerImportError(
                    module.__name__, manager_name, e))
                continue

            if not detect:
                logger.info('Manager %s.%s not detected',
                            module.__name__, manager_name)
                continue

            try:
                manager = self.setup(obj)
            except NapixImportError as e:
                errors.append(e)
            except Exception as e:
                errors.append(ManagerImportError(
                    module.__name__, manager_name, e))
            else:
                logger.info('Found Manager %s.%s', module.__name__, manager_name)
                managers.append(ManagerImport(
                    manager, manager.get_name(), self.get_config_from(manager)))

        return managers, errors

    def get_config_from(self, manager):
        """
        Tries to find the configuration for this manager.

        It parses the JSON inside the docstring of the method
        :meth:`~napixd.managers.base.Manager.configure`
        """
        parser = ''
        try:
            doc_string = manager.configure.__doc__ or ''
            doc_string = doc_string.strip()

            if not doc_string:
                return EmptyConf()

            if doc_string.startswith('{'):
                parser = 'json'
                # JSON object
                logger.debug('Parse JSON configuration')
                return JSONConfFactory().parse_string(doc_string)
            elif DotconfConfFactory is None:
                logger.warning('Cannot parse configuration with dotconf')
                return EmptyConf()
            else:
                parser = 'dotconf'
                logger.debug('Parse dotconf configuration')
                return DotconfConfFactory().parse_string(doc_string)

        except (ValueError, AttributeError) as e:
            logger.debug(
                'Auto configuration of %s from docstring failed using %s because %s',
                manager, parser, e)

        return EmptyConf()


class AutoImporter(BaseAutoImporter):
    """
    Imports all the modules in a directory

    It scans the directory for ``.py`` files,
    imports them and find all the Manager subclasses.
    """

    def get_paths(self):
        return [self.path]

    def load(self):
        """
        Explore the path to find modules.

        Any file with a ``.py`` extension is loaded.
        """
        # Placeholder module for all the auto imported modules
        import napixd.auto  # NOQA
        logger.debug('inspecting %s', self.path)
        managers, errors = [], []
        for filename in os.listdir(self.path):
            if filename.startswith('.') or not filename.endswith('.py'):
                continue

            try:
                module = self.import_module(filename)
            except NapixImportError as e:
                logger.warning('Failed to import %s from autoload: %s',
                               filename, str(e))
                errors.append(e)
                continue

            managers_, errors_ = self.load_module(module)
            managers.extend(managers_)
            errors.extend(errors_)
        return managers, errors

    def import_module(self, filename):
        module_name, x = filename.split('.')
        path = os.path.join(self.path, filename)
        name = 'napixd.auto.' + module_name

        if name in sys.modules and not self.has_been_modified(path, name):
            return sys.modules[name]

        logger.debug('Opening %s', path)
        with open(path, 'U') as handle:
            try:
                module = imp.load_module(
                    name,
                    handle,
                    path,
                    ('py', 'U', imp.PY_SOURCE),
                )
            except Exception as e:
                raise ModuleImportError(name, e)
        return module
