#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ('Wrapper', )


class cached_property(object):
    def __init__(self, fn):
        self.fn = fn
        self.__doc__ = fn.__doc__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        v = instance.__dict__[self.fn.__name__] = self.fn(instance)
        return v


class Wrapper(object):
    """
    This class encapsulate a *manager* and an *id*.

    The :attr:`resource` is the result of the call to
    :meth:`~napixd.managers.base.Manager.get_resource` with this *id*.

    .. attribute:: manager

        The manager on witch the operation is run

    .. attribute:: id

        The id of the resource
    """

    def __init__(self, manager, id, resource=None):
        self.manager = manager
        self.id = id
        if resource:
            self.resource = resource

    @cached_property
    def resource(self):
        """
        The value of the resource as retruned by
        :meth:`~napixd.managers.base.Manager.get_resource`

        This value is lazily loaded and cached.
        """
        return self.manager.get_resource(self.id)

    def __repr__(self):
        return 'Resource {0} of {1} {2}'.format(
            self.id, self.manager.get_name(),
            'loaded' if 'resource' in self.__dict__ else 'not loaded')

    def __eq__(self, other):
        return (
            isinstance(other, Wrapper) and
            self.manager == other.manager and
            self.id == other.id
        )
