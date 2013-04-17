#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import time
import os
import collections

from napixd.managers import Manager

logger = logging.getLogger('Napix.loader')

class ManagerImport(object):
    def __init__(self, manager, alias, config):
        self.manager = manager
        self.alias = alias
        self.config = config
    def __repr__(self):
        return '{0} "{1}"'.format( self.manager, self.alias)

    def __iter__(self):
        return iter( self._as_tuple())
    def _as_tuple(self):
        return ( self.manager, self.alias, self.config)
    def __hash__( self):
        return hash(( self.manager, self.alias))
    def __eq__(self, other):
        return isinstance( other, ManagerImport) and self._as_tuple() == other._as_tuple()
    def __ne__(self, other):
        return not self == other

ManagerError = collections.namedtuple( 'ManagerError', ( 'manager', 'alias', 'cause'))
Load = collections.namedtuple( 'Load', [ 'old_managers', 'managers', 'new_managers', 'error_managers'])

import_fn = __import__

class NapixImportError( Exception):
    pass

class ModuleImportError(NapixImportError):
    def __init__( self, module, cause):
        super( ModuleImportError, self).__init__( module, cause)
        self.module = module
        self.cause = cause

    def contains(self, manager):
        return self.module == manager.__module__

class ManagerImportError(NapixImportError):
    def __init__( self, module, manager, cause):
        super( ManagerImportError, self).__init__( module, manager, cause)
        self.module = module
        self.manager = manager
        self.cause = cause

    def contains(self, manager):
        return self.module == manager.__module__ and self.manager == manager.__name__

class Importer( object):
    def __init__(self, timestamp=0):
        self.timestamp = timestamp
        self.errors = []

    def first_import(self, module_path):
        #first module import
        logger.debug('import %s', module_path)
        try:
            import_fn(module_path)
        except ImportError as e:
            logger.error( 'Failed to import %s, %s', module_path, e)
            raise ModuleImportError( module_path, e)
        return sys.modules[module_path]

    def reload(self, module_path):
        logger.debug('reload %s', module_path)
        module = sys.modules[module_path]
        try:
            if module.__file__.endswith('pyc'):
                module_file = module.__file__[:-1]
            else:
                module_file = module.__file__

            last_modif = os.stat(module_file).st_mtime
            logger.debug( 'Module %s last modified at %s', module_path, last_modif)
        except OSError, e:
            logger.error( 'Failed to get file %s, %s', module_path, e)
            raise ModuleImportError( module_path, 'Module does not exists anymore')

        if last_modif > self.timestamp:
            #modified since last access
            logger.debug( 'Reloading module %s', module_path)
            try:
                reload( module)
            except ImportError as e:
                logger.error( 'Failed to reload %s, %s', module_path, e)
                raise ModuleImportError( module_path, e)
        return module

    def import_module( self, module_path ):
        if not isinstance( module_path, basestring):
            raise TypeError, 'module_path is a string'
        elif not module_path in sys.modules:
            return self.first_import( module_path)
        else:
            return self.reload( module_path)

    def import_manager(self, manager_path, reference=None):
        logger.debug('Import Manager %s', manager_path)
        if isinstance( manager_path, type) and issubclass( manager_path, Manager):
            module_path = manager_path.__module__
            manager_name = manager_path.__name__
        else:
            module_path, x, manager_name = manager_path.rpartition('.')

        if not module_path:
            if reference:
                module_path = reference.__module__
            else:
                raise ValueError( 'manager_path must contains the module name')

        module = self.import_module( module_path)
        try:
            return getattr( module, manager_name)
        except AttributeError as e:
            logger.error( 'Module %s does not contain %s', module_path, manager_name)
            raise ManagerImportError( module_path, manager_name, e)

class FixedImporter(Importer):
    def __init__(self, managers, timestamp=0):
        self.managers = managers
        super( FixedImporter, self).__init__( timestamp)

    def load( self):
        managers, errors = [], []
        for alias, spec in self.managers.items():
            try:
                manager, conf = spec
            except ValueError:
                manager, conf = spec, {}

            logger.info('Import fixed %s', manager)
            try:
                manager = self.import_manager( manager)
            except NapixImportError, e:
                errors.append( e)
            else:
                managers.append( ManagerImport( manager, alias, conf))
        return managers, errors

class ConfImporter(Importer):
    def __init__( self, conf, timestamp=0 ):
        super( ConfImporter, self).__init__( timestamp)
        self.conf = conf

    def load(self):
        """
        Load the managers with the conf
        return a list of Manager subclasses
        """
        managers, errors = [], []
        for alias, manager_path in self.conf.get('Napix.managers').items():
            try:
                manager = self.import_manager( manager_path )
                logger.info('load %s from conf', manager_path)
                config = self.conf.get( alias)
                import_ = ManagerImport( manager, alias, config)
            except NapixImportError, e:
                errors.append(e)
            else:
                managers.append( import_)
        return managers, errors


class AutoImporter(Importer):
    def __init__(self, path, timestamp=0):
        super( AutoImporter, self).__init__( timestamp)
        self.path = path
        if not self.path in sys.path:
            sys.path.append( self.path)

    def load( self):
        logger.debug( 'inspecting %s', self.path)
        managers, errors = [], []
        for filename in os.listdir(self.path):
            if filename.startswith('.'):
                continue
            module_name, dot, py = filename.rpartition('.')
            if not dot or py != 'py':
                continue

            managers_, errors_ = self.load_module( module_name)
            managers.extend( managers_)
            errors.extend( errors_)
        return managers, errors

    def load_module( self, module_name):
        try:
            module = self.import_module(module_name)
        except NapixImportError as e:
            logger.warning( 'Failed to import %s from autoload: %s', module_name, str(e))
            return [], [ e ]

        managers, errors = [], []
        content = getattr( module, '__all__', False) or dir( module)
        for manager_name in content:
            try:
                obj = getattr(module, manager_name)
            except AttributeError as e:
                errors.append( ManagerImportError( module_name, manager_name, e))
                continue

            if not isinstance( obj, type) or not issubclass( obj, Manager):
                 continue

            try:
                detect= obj.detect()
            except Exception as e:
                logger.error( 'Error while running detect of manager %s.%s', module_name, manager_name)
                errors.append( ManagerImportError( module_name, manager_name, e))
                continue

            if detect:
                managers.append( ManagerImport( obj, obj.get_name(), {}))
            else:
                logger.info('Manager %s.%s not detected', module_name, manager_name)

        return managers, errors

class RelatedImpoter(Importer):
    def __init__( self, reference, timestamp=0):
        super( RelatedImpoter, self).__init__( timestamp)
        self.reference = reference

    def load(self, classes):
        try:
            managers = [ self.import_manager( cls, reference=self.reference) for cls in classes ]
        except NapixImportError, e:
            return [], [ e ]
        else:
            return managers, []

class Loader( object):
    def __init__(self, importers):
        self.importers = importers.items() if isinstance( importers, dict) else list(importers)
        self.managers = set()
        self.errors = set()
        self.timestamp = 0
        self._already_loaded = set()

    def get_paths(self):
        return []

    def load(self):
        logger.info( 'Run a load')
        managers = set()
        import_errors = []

        for Importer, args in self.importers:
            importer = Importer( *args, timestamp=self.timestamp)
            imports, errors_ = importer.load()

            managers.update( imports)
            import_errors.extend( errors_)

        new_managers = managers.difference( self.managers)
        old_managers = self.managers.difference( managers)

        errors = set()
        for old in old_managers:
            for error in import_errors:
                if error.contains(old.manager):
                    errors.add( ManagerError( old.manager, old.alias,  error.cause))
                    break

        for import_ in list(new_managers):
            try:
                self.setup( import_.manager)
            except NapixImportError as e:
                managers.discard( import_)
                new_managers.discard( import_)
                old_managers.add( import_)
                errors.add( ManagerError( import_.manager, import_.alias, e))

        self.managers = managers
        self.timestamp = time.time()
        return Load( old_managers, managers, new_managers, errors)

    def setup( self, manager):
        if manager in self._already_loaded:
            raise ManagerImportError( manager.__module__, manager, ValueError('Circular dependency'))
        self._already_loaded.add( manager)

        if manager.direct_plug() is None:
            managed_classes = []
        else:
            importer = RelatedImpoter( manager, self.timestamp)
            managed_classes, errors = importer.load( manager.get_managed_classes() )
            if errors:
                raise ManagerImportError( manager.__module__, manager, errors[0])
            for managed_class in managed_classes:
                self.setup( managed_class)

        manager.set_managed_classes(managed_classes)
        return manager

