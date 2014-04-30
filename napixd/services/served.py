#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from napixd.services.requests import (
    ServiceCollectionRequest,
    ServiceResourceRequest,
)
from napixd.services.contexts import ResourceContext


class FirstServedManager(object):
    """
    Intermediary object the objects needed to serve a
    :class:`napixd.managers.Manager` class.

    It includes *configuration*, a :class:`napixd.conf.BaseConf` instance used
    to configure the instances, an :class:`napixd.service.urls.URL` at wich the
    manager is served.

    .. attribute:: manager_class

        The subclass of :class:`napixd.managers.Manager`
    """
    def __init__(self, manager_class, configuration, namespaces, lock=None):
        self.manager_class = manager_class
        self.configuration = configuration
        self.lock = lock
        self.namespaces = namespaces

    def __repr__(self):
        return '{0} at /{1}'.format(
            self.manager_class.get_name(),
            '/'.join(self.namespaces))

    def __eq__(self, other):
        return (isinstance(other, FirstServedManager) and
                self.manager_class == other.manager_class and
                self.configuration == other.configuration and
                self.namespaces == other.namespaces and
                self.lock == other.lock
                )

    def instantiate(self, resource, context):
        """
        Instantiates a :attr:`manager_class` with the parent resource and
        a :class:`napixd.services.contexts.ResourceContext`.

        It returns a :class:`ServedManagerInstance`.
        """
        context = ResourceContext(self, context)
        manager = self.manager_class(resource, context)
        manager.configure(self.configuration)
        return ServedManagerInstance(manager, context)

    @property
    def resource_fields(self):
        """
        The resource fields of the manager as a dict.
        """
        rf = self.manager_class._resource_fields
        return dict((key, dict(value)) for key, value in rf.items())

    @property
    def source(self):
        """
        The location of the code of the server manager class.
        """
        mc = self.manager_class
        return {
            'class': mc.__name__,
            'module': mc.__module__,
            'file': sys.modules[mc.__module__].__file__,
        }

    @property
    def meta_data(self):
        """
        All the meta datas of the manager.
        """
        mc = self.manager_class
        return {
            'doc': (mc.__doc__ or '').strip(),
            'direct_plug': False if mc.get_managed_classes() else None,
            'views': dict((format_, (cb.__doc__ or '').strip())
                          for (format_, cb)
                          in mc.get_all_formats().items()),
            'managed_class': [m.get_name() for m in mc.get_managed_classes()],
            'actions': dict((action, getattr(mc, action).__doc__)
                            for action in mc.get_all_actions()),
            'collection_methods': ServiceCollectionRequest.available_methods(mc),
            'resource_methods': ServiceResourceRequest.available_methods(mc),
            'resource_fields': self.resource_fields,
            'source': self.source,
        }

    def get_all_actions(self):
        """
        Returns a collection of :class:`ServedAction` for the actions
        of the served manager.
        """
        return [ServedAction(self, action)
                for action in self.manager_class.get_all_actions()]


class ServedManager(FirstServedManager):
    """
    The *extractor* is the extractor used for the managed classes.
    """
    def __init__(self, manager_class, configuration, namespaces, extractor, lock=None):
        super(ServedManager, self).__init__(manager_class, configuration, namespaces, lock)
        self.extractor = extractor

    def __eq__(self, other):
        return (super(ServedManager, self).__eq__(other) and
                self.extractor == other.extractor)

    def instantiate(self, resource, context):
        resource = self.extractor(resource)
        return super(ServedManager, self).instantiate(resource, context)


class ServedAction(object):
    """
    An intermediary object for an action of a :class:`ServedManager`.
    """
    def __init__(self, served_manager, action_name):
        self.name = action_name
        self.lock = served_manager.lock
        self.action = getattr(served_manager.manager_class, action_name)
        self.doc = (self.action.__doc__ or '').strip()
        self.source = served_manager.source
        self.source['method'] = self.action.__name__

    def __eq__(self, other):
        return (isinstance(other, ServedAction) and
                self.action == other.action
                )

    @property
    def resource_fields(self):
        rf = self.action.resource_fields
        return dict((key, dict(value)) for key, value in rf.items())

    @property
    def meta_data(self):
        return {
            'resource_fields': self.resource_fields,
            'doc': self.doc,
            'mandatory': self.action.mandatory,
            'optional': self.action.optional,
            'source': self.source,
        }


class ServedManagerInstance(object):
    """
    A class to bind a :class:`napixd.managers.Manager` instance and a
    :class:`napixd.services.contexts.ResourceContext`.

    The methods fill when it's relevant the ResourceContext.
    """
    def __init__(self, manager_instance, resource_context):
        self._manager_instance = manager_instance
        self._resource_context = resource_context
        self._resource_context.manager = manager_instance

    @property
    def manager(self):
        return self._manager_instance

    def __eq__(self, other):
        return (isinstance(other, ServedManagerInstance) and
                self._manager_instance == other._manager_instance and
                self._resource_context == other._resource_context)

    def __getattr__(self, attr):
        return getattr(self._manager_instance, attr)

    def validate_id(self, id):
        """
        Validates *id* with :meth:`napixd.managers.Manager.validate_id` and
        sets the :attr:`napixd.services.contexts.ResourceContext.id`.
        """
        id = self._manager_instance.validate_id(id)
        self._resource_context.id = id
        return id

    def get_resource(self):
        """
        Gets the resource at *id* with :meth:`napixd.managers.Manager.validate_id`
        and sets the :attr:`napixd.services.contexts.ResourceContext.resource`.
        """
        resource = self._manager_instance.get_resource(self._resource_context.id)
        wrapped = self._resource_context.make_resource(resource)
        self._resource_context.resource = wrapped
        return wrapped

    def __repr__(self):
        return 'SMI of {self._resource_context}'.format(self=self)
