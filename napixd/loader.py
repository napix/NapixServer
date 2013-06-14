#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modules loader for napix.

A :class:`Loader` instance finds and keeps tracks of modules
for the duration of the server.

It uses :class:`Importer` subclasses to find the its managers.
"""

import imp
import logging
import sys
import time
import os
import collections
import json

from napixd.managers import Manager
from napixd.conf import Conf

__all__ = ( 'Loader', 'Importer',
    'FixedImporter', 'ConfImporter', 'AutoImporter', 'RelatedImporter',
    'ManagerImport', 'NapixImportError', 'ManagerImportError',
    'ManagerError', 'Load'
    )

logger = logging.getLogger('Napix.loader')

class ManagerImport(object):
    """
    A manager import.

    It defines a *manager class* under a *name* with a *config*.
    """
    def __init__(self, manager, alias, config):
        self.manager = manager
        self.alias = alias
        self.config = config
    def __repr__(self):
        return '<Import {0} "{1}">'.format( self.manager, self.alias)

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
open = open

class NapixImportError( Exception):
    """
    Base Exception of loading errors.
    """
    pass

class ModuleImportError(NapixImportError):
    """
    An error when importing a module.
    All manager inside this module are unavailable.
    """
    def __init__( self, module, cause):
        super( ModuleImportError, self).__init__( module, cause)
        self.module = module
        self.cause = cause

    def contains(self, manager):
        return self.module == manager.__module__

class ManagerImportError(NapixImportError):
    """
    An error when importing a manager.

    This manager is the only one impacted.
    """
    def __init__( self, module, manager, cause):
        super( ManagerImportError, self).__init__( module, manager, cause)
        self.module = module
        self.manager = manager
        self.cause = cause

    def contains(self, manager):
        return self.module == manager.__module__ and self.manager == manager.__name__

class Importer( object):
    """
    The base class of the manager importers.

    Subclasse must define a :meth:`load` method that will use :meth:`import_manager`
    and :meth:`import_module` to find on its location.
    """
    def __init__(self, raise_on_first_import=True):
        self.timestamp = 0
        self.errors = []
        self.raise_on_first_import = raise_on_first_import

    def get_paths(self):
        """
        Return the paths watched by this manager.
        """
        return []

    def set_timestamp( self, timestamp):
        self.timestamp = timestamp

    def load(self):
        """
        Do the loading.

        It must return a tuple of two iterables, *managers* and *errors*
        *managers* is an iterable of :class:`~napixd.managers.base.Manager` sub-classes.
        *errors* are the errors that happended during the loading.
        """
        raise NotImplementedError

    def first_import(self, module_path):
        """
        Import the module for the first time.
        """
        #first module import
        logger.debug('import %s', module_path)
        try:
            import_fn(module_path)
        except (Exception, ImportError) as e:
            if self.raise_on_first_import:
                raise
            logger.error( 'Failed to import %s, %s', module_path, e)
            raise ModuleImportError( module_path, e)
        return sys.modules[module_path]

    def reload(self, module_path):
        """
        Try to reload the module if it was modified since the last time.
        """
        module = sys.modules[module_path]
        try:
            if module.__file__.endswith('pyc'):
                module_file = module.__file__[:-1]
            else:
                module_file = module.__file__

            last_modif = os.stat(module_file).st_mtime
            logger.debug( 'Module %s last modified at %s > %s', module_path, last_modif, self.timestamp)
        except OSError, e:
            logger.error( 'Failed to get file %s, %s', module_path, e)
            raise ModuleImportError( module_path, 'Module does not exists anymore')

        if last_modif > self.timestamp:
            #modified since last access
            logger.debug( 'Reloading module %s', module_path)
            try:
                reload( module)
            except Exception as e:
                logger.error( 'Failed to reload %s, %s', module_path, e)
                raise ModuleImportError( module_path, e)
        return module

    def import_module( self, module_path ):
        """
        imports a module.
        """
        if not isinstance( module_path, basestring):
            raise TypeError, 'module_path is a string'
        elif not module_path in sys.modules or self.timestamp == 0:
            return self.first_import( module_path)
        else:
            return self.reload( module_path)

    def import_manager(self, manager_path, reference=None):
        """
        Imports a manager.

        *manager_path* is a :class:`~napixd.managers.base.Manager`,
        a full path to a Manager subclass or a name in the *reference* module.

        *reference* is used only when *manager_path* is just a name.
        """
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
    """
    Imports a list of managers.

    It takes a *managers* dict of the service name mapping
    to either a tuple ( :class:`Manager subclass<napixd.managers.base.Manager>`, config)
    or just the Manager subclass.

    >>>FixedImporter({
        'this' : ( ThisManager, { 'a' : 1 }),
        'that' : ThatManager
        })
    """
    def __init__(self, managers):
        super( FixedImporter, self).__init__()
        self.managers = managers

    def load( self):
        managers, errors = [], []
        for alias, spec in self.managers.items():
            try:
                manager, conf = spec
            except ValueError:
                manager, conf = spec, Conf()
            else:
                if not isinstance( conf, Conf):
                    conf = Conf( conf)

            logger.info('Import fixed %s', manager)
            try:
                manager = self.import_manager( manager)
            except NapixImportError, e:
                errors.append( e)
            else:
                managers.append( ManagerImport( manager, alias, conf))
        return managers, errors

class ConfImporter(Importer):
    """
    Imports the manager as specified in the config file.:

    It refers to the :ref:`conf.napix.managers` to find the managers name.

    The config of each manager is found in the :mod:`default configuration<napixd.conf>` of Napix.
    """
    def __init__( self, conf):
        super( ConfImporter, self).__init__()
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
    """
    Imports all the modules in a directory

    It scans the directory for ``.py`` files,
    imports them and find all the Manager subclasses.
    """
    def __init__(self, path):
        super( AutoImporter, self).__init__( False)
        self.path = path
        if not self.path in sys.path:
            sys.path.append( self.path)

    def get_paths(self):
        return [ self.path ]

    def load( self):
        """
        Explore the path to find modules.

        Any file with a ``.py`` extension is loaded.
        """
        import napixd.auto
        logger.debug( 'inspecting %s', self.path)
        managers, errors = [], []
        for filename in os.listdir(self.path):
            if filename.startswith('.') or not filename.endswith('.py'):
                continue

            try:
                module = self.import_module( filename)
            except NapixImportError as e:
                logger.warning( 'Failed to import %s from autoload: %s', filename, str(e))
                errors.append( e)
                continue

            managers_, errors_ = self.load_module( module)
            managers.extend( managers_)
            errors.extend( errors_)
        return managers, errors

    def import_module( self, filename):
        module_name, x = filename.split('.')
        path = os.path.join( self.path, filename)

        name = 'napixd.auto.' + module_name
        with open( path, 'U') as handle:
            try:
                module = imp.load_module(
                        name,
                        handle,
                        path,
                        ( 'py', 'U', imp.PY_SOURCE),
                        )
            except ( Exception, ImportError) as e:
                raise ModuleImportError( name, e)
        return module

    def load_module( self, module):
        """
        Explore a module and search for :class:`napixd.managers.base.Manager` subclasses.
        The method :meth:`~napixd.managers.base.Manager.detect` is called and
        if it returns False, the manager is ignored.

        The configuration is loaded from the docstring of the :meth:`~napixd.managers.base.Manager.configure`  method.
        """

        managers, errors = [], []
        content = getattr( module, '__all__', False) or dir( module)
        for manager_name in content:
            try:
                obj = getattr(module, manager_name)
            except AttributeError as e:
                errors.append( ManagerImportError( module.__name__, manager_name, e))
                continue

            if not isinstance( obj, type) or not issubclass( obj, Manager):
                 continue

            try:
                detect= obj.detect()
            except Exception as e:
                logger.error( 'Error while running detect of manager %s.%s', module.__name__, manager_name)
                errors.append( ManagerImportError( module.__name__, manager_name, e))
                continue

            if detect:
                managers.append( ManagerImport( obj, obj.get_name(), self.get_config_from( obj)))
            else:
                logger.info('Manager %s.%s not detected', module.__name__, manager_name)

        return managers, errors

    def get_config_from( self, manager):
        try:
            doc_string = manager.configure.__doc__
            if doc_string:
                return Conf( json.loads( doc_string))
        except ( ValueError, AttributeError) as e:
            logger.debug( 'Auto configuration of %s from docstring failed because %s', manager, e)

        return Conf({})


class RelatedImporter(Importer):
    """
    Imports the managed classes.

    The *reference* parameter is a manager class.
    The submanager classes are searched in the same module than the *reference* class
    if the path does not contains ``.``
    """
    def __init__( self, reference):
        super( RelatedImporter, self).__init__()
        self.reference = reference

    def load(self, classes):
        logger.debug('loading related classes')
        managed_classes = []
        for cls in classes:
            if not cls.is_resolved():
                try:
                    managed_class = self.import_manager( cls.path, reference=self.reference)
                    cls.resolve( managed_class)
                except NapixImportError, e:
                    return [], [ e ]
            managed_classes.append( cls.manager_class)
        return managed_classes, []

class Loader( object):
    """
    Finds and keeps track of the managers.

    The loader takes a list of :class:`Importer` instances.
    Each time the loader runs a loading cycle,
    it calls the :meth:`Importer.load` on each of them and gets
    the managers and errors.

    The managers set is compared to the previous and a :class:`Load` object is created
    with the new and the olds managers
    """
    def __init__(self, importers):
        self.importers = importers
        self.managers = set()
        self.errors = set()
        self.timestamp = 0
        self._already_loaded = set()

    def get_paths(self):
        """
        List the paths to watch with :mod:`napixd.reload`
        """
        paths = []
        for importer in self.importers:
            paths.extend( importer.get_paths())
        return paths

    def load(self):
        """
        Run a loading cycle
        """
        logger.info( 'Run a load at %s', self.timestamp)
        managers = set()
        import_errors = []

        for importer in self.importers:
            importer.set_timestamp( self.timestamp)
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
        """
        Loads the managed classes of a manager
        """
        if manager in self._already_loaded:
            raise ManagerImportError( manager.__module__, manager, ValueError('Circular dependency'))
        self._already_loaded.add( manager)

        if manager.direct_plug() is not None:
            importer = RelatedImporter( manager)
            managed_classes, errors = importer.load( manager.get_managed_classes() )
            if errors:
                raise ManagerImportError( manager.__module__, manager, errors[0])
            for managed_class in managed_classes:
                self.setup( managed_class)

        return manager

