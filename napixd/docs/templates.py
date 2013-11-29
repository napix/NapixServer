#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Templates for the documentation generator.

Each template is a class associated to a type of object to document.
The classes are responsible for the creation and
rendering of sub-templates recursively.
"""

from napixd.docs.rendering import DocStrings, DocString, Context


class LoaderDocTemplate(object):
    """
    The base template for a :class:`napixd.loader.loader.Loader` instance.
    """
    def __init__(self, loader):
        self.root_managers = map(RootDocTemplate, loader.managers)

    def render(self, context):
        return [rm.render(context) for rm in self.root_managers]


class DocTemplate(object):
    """
    A base class for managers classes.
    """
    def __init__(self, manager):
        self.manager = manager
        self.resource_doc = ResourceDocTemplate(manager)
        self.collection_doc = CollectionDocTemplate(manager)
        self.fields_doc = ResourceFieldsDocTemplate(manager._resource_fields)
        self.sub_managers_docs = [ManagedClassDocTemplate(managed_class)
                                  for managed_class
                                  in manager.get_managed_classes()]

    def render(self, context):
        return {
            'docstring': DocString(self.manager),
            'fields': self.fields_doc.render(context),
            'collection': self.collection_doc.render(context),
            'resource': self.resource_doc.render(context),
            'managers': [smd.render(context) for smd in self.sub_managers_docs],
        }


class RootDocTemplate(DocTemplate):
    """
    The template for root managers.

    All sub-managers and their sub-managers are rendered
    by a :class:`ManagedClassDocTemplate`
    """
    def __init__(self, manager_import):
        super(RootDocTemplate, self).__init__(manager_import.manager)
        self.alias = manager_import.alias

    def render(self, context):
        context = Context(context)
        context['url'] = ['', self.alias]
        context['manager'] = self.manager
        context['anchor'] = self.alias
        rendered = super(RootDocTemplate, self).render(context)
        rendered.update({
            'anchor': context['anchor'],
            'alias': self.alias,
        })
        return rendered


class ManagedClassDocTemplate(DocTemplate):
    def __init__(self, managed_class):
        super(ManagedClassDocTemplate, self).__init__(
            managed_class.manager_class)
        self.alias = managed_class.get_name()

    def render(self, context):
        context = Context(context)
        context['anchor'] += '/' + self.alias
        context['url'].append(self.alias)
        return super(ManagedClassDocTemplate, self).render(context)


class ResourceFieldsDocTemplate(object):
    """
    A template class for :attr:`napxixd.managers.resource_fields.ResourceFields`
    """
    def __init__(self, resource_fields):
        self.rf = resource_fields

    def render(self, context):
        return dict(zip(self.rf, map(dict, self.rf.values())))


class CollectionDocTemplate(object):
    """
    A template class for the collection side of managers.
    """
    def __init__(self, manager):
        self.has_list = (hasattr(manager, 'list_resource') or
                         hasattr(manager, 'get_all_resources') or
                         hasattr(manager, 'get_all_resources_filter'))
        self.has_filters = (hasattr(manager, 'list_resource_filters') or
                            hasattr(manager, 'get_all_resources_filter'))
        self.has_create = hasattr(manager, 'create_resource')

        ds = DocStrings(manager)
        self.list_resource = ds.list_resource
        self.list_resource_filters = ds.list_resource_filters
        self.create_resource = ds.create_resource

    def get_implemented_methods(self):
        methods = []
        if self.has_list:
            methods.append('GET')
        if self.has_create:
            methods.append('POST')
        return methods

    def render(self, context):
        context = Context(context)
        url = context['url']
        url.append('')

        return {
            'methods': self.get_implemented_methods(),
            'anchor': context['anchor'] + '/',
            'url': '/'.join(url),
            'GET': self.list_resource,
            'filters': self.list_resource_filters,
            'POST': self.create_resource,
        }


class ViewDocTemplate(object):
    """
    The template for the :func:`napixd.managers.views.view`
    """
    def __init__(self, manager, view, method):
        self.view = view
        self.method = method

    def render(self, context):
        url = context['url']
        return {
            'url': '/'.join(url) + '?format=' + self.view,
            'anchor': context['anchor'] + '/' + self.view,
            'view': self.view,
            'docstring': DocString(self.method),
        }


class ActionDocTemplate(object):
    """
    The template for the :func:`~napixd.managers.actions.action`
    """
    def __init__(self, manager, action):
        self.action = action
        self.method = getattr(manager, action)
        self.fields_doc = ResourceFieldsDocTemplate(
            self.method.resource_fields)

    def render(self, context):
        context = Context(context)
        url = context['url']
        url.extend(['_napix_action', self.action])
        return {
            'url': '/'.join(url),
            'anchor': context['anchor'] + '/' + self.action,
            'action': self.action,
            'docstring': DocString(self.method),
            'fields': self.fields_doc.render(context),
        }


class ResourceDocTemplate(object):
    """
    A template class for the resource side of managers.
    """
    def __init__(self, manager):
        self.manager = manager
        self.has_get = (hasattr(manager, 'get_resource') or
                        hasattr(manager, 'get_all_resources') or
                        hasattr(manager, 'get_all_resources_filter'))
        self.has_modify = hasattr(manager, 'modify_resource')
        self.has_delete = hasattr(manager, 'delete_resource')
        self.views_docs = [ViewDocTemplate(manager, view, method)
                           for view, method in manager.get_all_formats().items()]
        self.actions_docs = [ActionDocTemplate(manager, action)
                             for action in manager.get_all_actions()]
        ds = DocStrings(manager)
        self.get_resource = ds.get_resource
        self.modify_resource = ds.modify_resource
        self.delete_resource = ds.delete_resource

    def get_resource_name(self):
        if self.manager.__name__.endswith('Manager'):
            return self.manager.__name__.lower()[:-7]
        return 'resource'

    def get_implemented_methods(self):
        methods = []
        if self.has_get:
            methods.append('GET')
        if self.has_modify:
            methods.append('PUT')
        if self.has_delete:
            methods.append('DELETE')
        return methods

    def render(self, context):
        url = context['url']
        url.append('{{{0}}}'.format(self.get_resource_name()))

        context = Context(context)
        context['anchor'] += '/resource'

        return {
            'methods': self.get_implemented_methods(),
            'anchor': context['anchor'],
            'url': '/'.join(url),
            'GET': self.get_resource,
            'PUT': self.modify_resource,
            'DELETE': self.delete_resource,
            'actions': [ad.render(context) for ad in self.actions_docs],
            'views': [vd.render(context) for vd in self.views_docs],
        }
