#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.exceptions import NotFound
from napixd.managers.base import ManagerInterface

METHODS = [method for method in vars(
    ManagerInterface) if not method.startswith('_')]


class Implementation(object):

    def __init__(self, manager):
        self.manager = manager
        self.methods = {}
        self.methods.update((name, getattr(manager, name))
                            for name in METHODS
                            if hasattr(manager, name))
        if len(self.methods) == len(METHODS):
            return

        for generic in [
                ByFilter_get_all_resources,
                ByFilter_list_resource,
                FromAll_get_resource,
                FromAll_list_resource,
                FromAll_list_resource_filter,
                CombinedFromAll_get_all_resources_filter,
                Combined_get_all_resources_filter,
                Combined_get_all_resources,
        ]:
            if (generic.implement not in self and
                    set(self).issuperset(generic.require)):
                self.methods[generic.implement] = generic(self)
                if len(self.methods) == len(METHODS):
                    break

    def __contains__(self, name):
        return name in self.methods

    def __iter__(self):
        return iter(self.methods)

    def __getattr__(self, name):
        if name in self.methods:
            return self.methods[name]
        return getattr(self.manager, name)


class BaseImplementer(object):

    def __init__(self, manager):
        self.manager = manager


class Combined_get_all_resources(BaseImplementer):
    implement = 'get_all_resources'
    require = ['get_resource', 'list_resource']

    def __call__(self):
        return [(id, self.manager.get_resource(id))
                for id in self.manager.list_resource()]


class ByFilter_get_all_resources(BaseImplementer):
    implement = 'get_all_resources'
    require = ['get_all_resources_filter']

    def __call__(self):
        return self.manager.get_all_resources_filter({})


class FromAll_get_resource(BaseImplementer):
    implement = 'get_resource'
    require = ['get_all_resources']

    def __call__(self, id_):
        for id, resource in self.get_all_resources():
            if id == id_:
                return resource
        raise NotFound(id_)


class FromAll_list_resource(BaseImplementer):
    implement = 'list_resource'
    require = ['get_all_resources']

    def __call__(self, manager):
        return [id for (id, resource) in self.manager.get_all_resources()]


class ByFilter_list_resource(BaseImplementer):
    implement = 'list_resource'
    require = ['list_resource_filter']

    def __call__(self):
        return self.manager.list_resource_filter({})


class Combined_get_all_resources_filter(BaseImplementer):
    implement = 'get_all_resources_filter'
    require = ['list_resource_filter', 'get_resource']

    def __call__(self, filters):
        return [(id, self.manager.get_resource(id))
                for id in self.manager.list_resource_filter(filters)]


class CombinedFromAll_get_all_resources_filter(BaseImplementer):
    implement = 'get_all_resources_filter'
    require = ['list_resource_filter', 'get_all_resources']

    def __call__(self, filters):
        ids = set(self.manager.list_resource_filter(filters))
        return [(id, resource)
                for id, resource in self.manager.get_all_resources()
                if id in ids
                ]


class FromAll_list_resource_filter(BaseImplementer):
    implement = 'list_resource_filter'
    require = ['get_all_resources_filter']

    def __call__(self, filters):
        return [id for id, resource in self.manager.get_all_resources_filter(filters)]
