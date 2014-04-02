#!/usr/bin/env python
# -*- coding: utf-8 -*-


import collections

__all__ = ('ResourceWrapper', )


class setable_property(object):
    def __init__(self, fn):
        self.fn = fn
        self.__doc__ = fn.__doc__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.fn(instance)


class ResourceWrapper(collections.Mapping):
    """
    This class encapsulate a *manager* and an *id*.

    The :attr:`resource` is the result of the call to
    :meth:`~napixd.managers.base.ManagerInterface.get_resource` with this *id*.

    .. attribute:: manager

        The manager on witch the operation is run

    .. attribute:: id

        The id of the resource
    """

    def __init__(self, manager, id, resource=None):
        self.manager = manager
        self.id = id
        if resource:
            self._set_resource(resource)

    def _set_resource(self, r):
        self._is_a_dict = isinstance(r, collections.Mapping)
        self.resource = r
        return r

    @property
    def request(self):
        return self.manager.request

    @property
    def loaded(self):
        return 'resource' in self.__dict__

    def __nonzero__(self):
        self.resource
        return True

    def __len__(self):
        return len(self._ensure_is_dict())

    def __iter__(self):
        return iter(self._ensure_is_dict())

    def __getitem__(self, item):
        return self._ensure_is_dict()[item]

    def _ensure_is_dict(self):
        r = self.resource
        if not self._is_a_dict:
            raise ValueError('Proxy getitem is only available on Mapping instances')
        return r

    @setable_property
    def resource(self):
        """
        The value of the resource as retruned by
        :meth:`~napixd.managers.base.Manager.get_resource`

        This value is lazily loaded and cached.
        """
        return self._set_resource(self.manager.get_resource(self.id))

    def __repr__(self):
        return 'Resource {0} of `{1}` {2}'.format(
            self.id, self.manager.get_name(),
            'loaded' if self.loaded else 'not loaded')

    def __eq__(self, other):
        return (
            isinstance(other, ResourceWrapper) and
            self.manager == other.manager and
            self.id == other.id
        )
