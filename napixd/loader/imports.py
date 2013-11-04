#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Structures used by the :class:`napixd.loader.loader.Loader`
to transfer the manager to the application.
"""


class ManagerImport(object):

    """
    A manager import.

    It defines a *manager class* under a *name* with a *config*.

    .. attribute:: manager

        A :class:`napixd.manager.Manager` subclass.

    .. attribute:: alias

        The name under wich this manager is loaded.

    .. attribute:: config

        The :class:`napixd.conf.Conf` used to configure this service.
    """

    __slots__ = ('manager', 'alias', 'config')

    def __init__(self, manager, alias, config):
        self.manager = manager
        self.alias = alias
        self.config = config

    def __repr__(self):
        return '<Import {0} "{1}">'.format(self.manager.__name__, self.alias)

    def __hash__(self):
        return hash((self.manager, self.alias))

    def __eq__(self, other):
        return (isinstance(other, ManagerImport) and
                self.manager == other.manager and
                self.alias == other.alias and
                self.config == other.config)

    def __ne__(self, other):
        return not self == other


class ManagerError(object):
    """
    An object representing the exception *cause*
    interfering with the loading of *manager* with *alias*

    .. attribute:: cause

        The exception wich caused this error

    .. attribute:: alias

        The alias of the manager loaded.

    .. attribute:: manager

        The manager class being loaded
    """
    __slots__ = ('manager', 'alias', 'cause')

    def __init__(self, manager, alias, cause):
        self.manager = manager
        self.alias = alias
        self.cause = cause

    def __hash__(self):
        return hash((self.manager, self.alias, self.cause))

    def __eq__(self, other):
        return (isinstance(other, ManagerError) and
                self.alias == other.alias and
                self.manager == other.manager and
                self.cause == other.cause)
