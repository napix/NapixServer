#!/usr/bin/env python
# -*- coding: utf-8 -*-


class cached_property(object):
    def __init__(self, fn):
        self.fn = fn

    def __get__(self, instance, owner):
        if instance is None:
            return self.fn
        v = instance.__dict__[self.fn.__name__] = self.fn(instance)
        return v


class Wrapper(object):
    def __init__(self, manager, id, resource=None):
        self.manager = manager
        self.id = id
        if resource:
            self.resource = resource

    @cached_property
    def resource(self):
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
