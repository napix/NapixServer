#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Contexts objects for the services.

Context binds a :class:`napixd.managers.Manager`,
a :class:`napixd.services.collection.CollectionService`, or any other *napixd*
object with the request. They provides shortcuts for the instantiation of
managers and factories to get a manager or a resource from a
:class:`napixd.managers.Manager` instance.
"""

from napixd.services.requests.resource import (
    FetchResource
)
from napixd.services.wrapper import ResourceWrapper


class NapixdContext(object):
    """
    This context is instantiated with the current :class:`napixd.http.request.Request`
    instance and the :class:`napixd.application.Napixd` by the
    :class:`~napixd.application.Napixd`

    This objects binds the napixd instance with the request.

    .. attribute:: napixd

        The :class:`napixd.application.Napixd` instance on which the request is made.

    .. attribute:: request

        The original request.

    .. attribute:: method

        The http method of the original request.

    .. attribute:: data

        The data of the request.

    .. attribute:: parameters

        The parameters of the request. The GET of the *requet* is used by default.
    """
    def __init__(self, napixd, request):
        self.request = request
        self.napixd = napixd
        self.method = request.method
        self.parameters = request.GET
        self.data = request.data

    def get_service(self, service):
        """
        Finds a :class:`napixd.services.Service` by its name in the :attr:`napixd`
        """
        return self.napixd.find_service(service)

    def __repr__(self):
        return 'Napix context of {0} in {1}'.format(self.request, self.napixd)

    def __eq__(self, other):
        return (isinstance(other, NapixdContext) and
                self.napixd == other.napixd and
                self.request == other.request)


class CollectionContext(object):
    """
    This context is instantiated by the :class:`napixd.services.collection.CollectionService`
    with the :class:`NapixdContext`.
    """
    def __init__(self, cs, napixd_context, method=None):
        self.napixd = napixd_context
        self.service = cs
        if method is not None:
            self.method = method

    def __repr__(self):
        return 'Collection Context ({0})'.format(self.service)

    def __eq__(self, other):
        return (
            isinstance(other, CollectionContext) and
            self.napixd == other.napixd and
            self.service == other.service)

    def __getattr__(self, attr):
        return getattr(self.napixd, attr)

    def get_manager_instance(self, path):
        """
        Returns an instance of the manager
        """
        return self.service.get_manager(path, self)

    def get_collection_service(self, namespaces):
        """
        Returns the :class:`napixd.service.collection.CollectionService`
        serving requests for the given namespace.

        If there is not :class:`~napixd.service.collection.CollectionService`
        at this namespace, a :exc:`napixd.exceptions.InternalRequestFailed` is raised.
        """
        service = self.napixd.get_service(namespaces[0])
        cs = service.get_collection_service(namespaces)
        return cs

    def get_resource(self, url):
        """
        Fetches the resource at *url*.
        URL is a resource URL starting and not ending with a **/**.

        This method will raise :exc:`napixd.exceptions.InternalRequestFailed`
        if there is no resource at this URL.
        """
        path = url.split('/')
        if path[0] != '':
            raise ValueError('get_resource is called with a path starting by a "/"')
        if path[-1] == '':
            raise ValueError('get_resource is called with a path not ending with a "/"')

        # Takes the name segments
        managers = path[1::2]
        # Takes all the ID segments
        ids = path[2::2]
        cs = self.get_collection_service(managers)

        resource = FetchResource(
            CollectionContext(cs, self.napixd, method='GET'), ids)
        return resource.handle()


class maybe(object):
    """
    Raise a :exc:`ValueError` if the property is accessed without
    having been set.
    """
    def __init__(self, fn):
        self.fn = fn
        self.__doc__ = fn.__doc__
        self.__name__ = fn.__name__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        try:
            return instance.__dict__[self.__name__]
        except KeyError:
            raise ValueError('{name} has not been set before being accessed'.format(
                name=self.__name__))

    def __set__(self, instance, value):
        self.fn(instance)
        instance.__dict__[self.__name__] = value


class ResourceContext(object):
    """
    This context is instantiated by the :class:`napixd.services.served.ServedManager`.
    with the :class:`CollectionContext`.
    """
    def __init__(self, served_manager, collection_context):
        self.served_manager = served_manager
        self.collection_context = collection_context
        self.has_manager = False
        self.has_id = False
        self.has_resource = False

    @maybe
    def manager(self):
        """
        The :class:`napixd.managers.Manager` instance
        """
        self.has_manager = True

    @maybe
    def resource(self):
        """
        The :class:`napixd.services.wrapper.ResourceWrapper`
        served by the :attr:`manager`.
        """
        self.has_resource = True

    @maybe
    def id(self):
        """
        The id (validated) of the :attr:`resource`.
        """
        self.has_id = True

    def __eq__(self, other):
        return (isinstance(other, ResourceContext) and
                self.served_manager == other.served_manager and
                self.collection_context == other.collection_context
                )

    def __repr__(self):
        return 'ResourceContext of {0}'.format(self.collection_context)

    def __getattr__(self, attr):
        return getattr(self.collection_context, attr)

    def get_sub_manager(self, alias, resource=None):
        """
        Return the sub manager instance *alias* of the current :attr:`resource`.

        If the context does not have a :attr:`resource` yet, but the resource content is known,
        for example during the :meth:`~napixd.managers.Manager.get_resource` invocation,
        the resource should be given to the method via the *resource* argument.

        This method will raise :exc:`napixd.exceptions.InternalRequestFailed`
        if there is no manager with this *alias*.
        """
        if self.has_resource:
            r = self.resource
        else:
            r = self.make_resource(resource)

        ns = self.served_manager.namespaces + (alias, )
        cs = self.collection_context.get_collection_service(ns)
        return cs.served_manager.instantiate(r, self.collection_context)

    def make_resource(self, resource):
        """
        Make a resource with the know :attr:`manager` and :attr:`id` and the given *resource*.
        """
        return ResourceWrapper(self.manager, self.id, resource)
