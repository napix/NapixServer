#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manager :
    - manages a set of resources
    - does it by defining create/delete/modify methods that act on those resourcess

Ressource :
    - MUST be a dict (or an emulation thereof) that hold a set of properties
    - They MAY have actions

Manager are created by the corresponding resource
"""

import types
import collections

from napixd.exceptions import ValidationError, ImproperlyConfigured
from napixd.managers.managed_classes import ManagedClass
from napixd.managers.resource_fields import ResourceFields
from napixd.managers.actions import ActionProperty
from napixd.managers.changeset import DiffDict

__all__ = ('ManagerType', 'Manager', 'ManagerInterface')


class ManagerType(type):
    """
    Metaclass to create manager classes.

    It does 2 things:

    * resource_fields transformation

    It instantiates a :class:`resource_fields.ResourceFields`
    property for the `Manager.resource_fields` attribute.

    * Forwarding of :mod:`~napixd.managers.actions` and :mod`~napixd.managers.views`

    The :func:`~napixd.managers.actions.action` and
    :func:`napixd.managers.views.view` of the base classes
    are forwarded in the newly created class.

    """

    def __new__(self, name, bases, attrs):
        try:
            rf = attrs['resource_fields']
        except KeyError:
            pass
        else:
            try:
                attrs['_resource_fields'] = ResourceFields(rf)
            except ImproperlyConfigured as e:
                raise ImproperlyConfigured('In {0}, field {1}'.format(name, e))

        return super(ManagerType, self).__new__(self, name, bases, attrs)

    def __init__(self, name, bases, attrs):
        super(ManagerType, self).__init__(name, bases, attrs)

        self._managed_class = self._cast_managed_class()

        methods = [(attr_name, meth)
                   for attr_name, meth in attrs.items()
                   if not name.startswith('_')]

        self._all_actions = self._cast_actions(bases, methods)
        self._all_formats = self._cast_formats(bases, methods)

    def _cast_actions(self, bases, attrs):
        actions = []
        for base in bases:
            if hasattr(base, 'get_all_actions'):
                actions.extend(base.get_all_actions())

        for attribute_name, attribute in attrs:
            if isinstance(attribute, ActionProperty):
                actions.append(attribute_name)
        return actions

    def _cast_formats(self, bases, attrs):
        formats = {}
        for base in bases:
            if hasattr(base, 'get_all_formats'):
                formats.update(base.get_all_formats())

        formats.update((attribute._napix_view, attribute)
                       for attribute_name, attribute in attrs
                       if (hasattr(attribute, '_napix_view') and
                           attribute._napix_view))
        return formats

    def _cast_managed_class(self):
        if self.managed_class is None:
            return []

        if isinstance(self.managed_class, (basestring, ManagerType)):
            raise ImproperlyConfigured('Depreciation Error, direct_plug=True of {0}.'
                                       '{1} are not supported anymore'.format(
                                           self.__module__, self.__name__))

        if not isinstance(self.managed_class, collections.Iterable):
            raise ImproperlyConfigured('managed_class attribute of {0} is not an list'.format(
                self.__name__))

        managed_classes = list(self.managed_class)
        for i, managed_class in enumerate(managed_classes):
            if isinstance(managed_class, ManagedClass):
                continue
            managed_classes[i] = ManagedClass(managed_class)
        return managed_classes

    def get_managed_classes(self):
        """
        List the managed classes of this manager.

        It is always a list.
        """
        return self._managed_class

    def get_all_actions(self):
        """
        Returns the list of all the action implemented by this class.
        """
        return self._all_actions

    def get_all_formats(self):
        """
        Returns the dict of the formats implemented by this class.

        The keys are the name of the views and the values
        are the corresponding methods.
        """
        return self._all_formats

    def __repr__(self):
        return 'Manager class {module}:{cls} `{name}`'.format(
            module=self.__module__,
            cls=self.__name__,
            name=self.get_name(),
        )

    def implements(self):
        """
        Returns a set of implemented methods.
        """
        base = set(attr for attr in dir(self) if not attr.startswith('_'))
        return base.intersection(ManagerInterface.__dict__)


class Manager(object):

    """
    Base class of the managers

    Managers are objects created to serve requests
    on a resource for its sub resources
    exemple:
    GET /physics/constants/c
    A manager is created of the resource `physics`,
    this resource is asked for its child `constants`,
    a manager for this resource `constant` is created,
    and this manager is asked for its child `c`.
    The resource got is serialized and sent back to the user

    Managers cycle of life MAY contains multiple request,
    that MAY be executed simultaneously.

    The cycle of life is :

    - Class creation
    - Insertion into the application inside the root manager or through a parent manager
    - Manager.configure is called with the settings of this class
    - An instance is generated for a resource

    * start_request is called
    * the appropriate method to respond to the request is called (get_resource, create_resource, etc)
    * end_request is called

    Subclasses MAY set a :attr:`managed_class` class attribute.
    If set, it must be either a class inheriting from this same base class
    (or implementing its interface) or a iterable of thoses classes.

    If it's a single class, the resources are wrapped
    in this class when going up a level in the URL.

    example::

        >>> class FirstManager(Manager):
        ...     managed_class = SecondManager

        >>> class SecondManager(Manager):
        ...     def list_resource(self):
        ...         return {}

        GET /first/second/third
        >>> second_resource = FirstManager().get_resource('second') #/first
        ... second_manager = SecondManager(second_resource)  # [..]/second
        ... return second_manager.get_resource('third')  # [..]/third

    If it's a tuple or a list of classes,
    the children have multiple subressource managers attached.
    The class in wich the children is wrapped depends on the url path
    example::

        >>> class Main(Manager):
        ...     managed_class = [ManagerA,ManagerB]
        ...
        ... class ManagerA(Manager):
        ...     pass
        ... class ManagerB(Manager):
        ...     pass

        GET /main/1
        >>> Main().get_resource(1)

        GET /main/1/
        [ 'A', 'B' ]

        GET /main/1/A/
        >>> ManagerA(Main().get_resource(1)).list_resource()

        GET /main/1/B/
        >>> ManagerB(Main().get_resource(1)).list_resource()

        GET /main/1/B/3
        >>> ManagerB(Main().get_resource(1)).get_resource(3)

    If it's not set, the manager does not have sub resources::

        GET /first/second/third/
        404 NOT FOUND
        GET /first/second/third/fourth
        404 NOT FOUND

    Subclasses of this class MUST define their own list of fields
    in the class attribute resource_fields.

    This attribute is a dict where the keys are the fields names and the values
    are the descriptions of those fields

    properties includes:

        - optional: if the value is optional
        - example: used for documentation and the example resource
        - description: describe the use of the resource
        - computed: This field is computed by the service and the user CAN NOT force it

        The resource fields options are described in detail in
        :class:`resource_fields.ResourceFields`

    .. code-block:: python

        class User(Manager):
            resource_fields = {
                'username': {
                    'description': 'POSIX username of the system account',
                    'example': 'dritchie'
                },
                'uid':{
                    'description': '''Unique identifier,
                    will be generated if not given''',
                    'optional': True
                },
                'gecos':{
                    'description': 'Comment on the user name',
                    'example': 'Dennis M. Ritchie'
                }
            }

    The resources may contains some fields
    that are not in the class' resource_fields.
    When the resource are serialized to be send in json,
    only the fields in resource_fields are extracted.

    This behavior may be usefull to pass privates values to the next managers.
    exemple::

        >>> class SectionManager(Manager):
        ...     def list_resource(self):
        ...         return self.context.resource['parser'].get_sections()
        >>> class File(Manager):
        ...     managed_class = SectionManager
        ...     fields = { 'path': {} }
        ...     def get_resource(self, id):
        ...         return { 'parser': Parser('/etc/'+id), 'path': '/etc'+id }

        GET /file/file1
        { "path" : "/etc/file1" }
        #No parser field sent

        GET /file/file1/
        [ "section1" , "section2"]
        #Parser was passed to list_resource through context

    .. attribute:: resource_fields

        The fields of the resources

        Each manager must declare the fields of the resources it generates.
        The resource_fields must be a :class:`dict`.
        The keys are the name of the fields and the values are dicts that are
        transformed to :class:`napixd.managers.resource_fields.ResourceField`

    .. attribute:: context

        The resource that spawned this manager.
        It is an instance of :class:`napixd.services.wrapper.ResourceWrapper`.

        `None` for the root managers.

    .. method:: validate_resource_FIELDNAME

        Validate the content of the field ``FIELDNAME``

        .. note::

            validate_resource_FIELDNAME does not actually exists.
            FIELDNAME have to be replaced by an actual field
            of :attr:`resource_fields`

    .. attribute:: auto_load

        A class level boolean to tell if the class is used by the Napixd,
        when the :class:`auto-loader<napixd.loader.AutoImporter>`
        browse a module.
    """

    __metaclass__ = ManagerType

    auto_load = True

    # list of the fields publicly available with their properties
    resource_fields = {}
    # Class or list of classes wrapping the children
    managed_class = None

    name = None

    @classmethod
    def get_name(cls):
        if cls.name is not None:
            return cls.name
        name = cls.__name__.lower()
        if name.endswith('manager'):
            name = name[:-len('manager')]
        return name

    def __init__(self, context, napix_context):
        """
        intialize the Manager with the wrapped resource *context* creating it

        example::

        >>> class FirstManager(Manager):
        ...     managed_class = 'SecondManager'

        >>> class SecondManager(Manager):
        ...     def list_resource(self):
        ...         return {}

        GET /first/second/
        >>> SecondManager(FirstManager.get_resource('second')).list_resource()

        """
        self.context = context
        self.napix_context = napix_context
        self.request = napix_context.request

    def __repr__(self):
        return '<Manager {module}:{cls} `{name}` of "{context}">'.format(
            module=self.__class__.__module__,
            cls=self.__class__.__name__,
            name=self.get_name(),
            context=self.context
        )

    def get_formatter(self, format_):
        # return the method instance of the formatter
        return types.MethodType(self.__class__.get_all_formats()[format_],
                                self, self.__class__)

    def configure(self, conf):
        """
        Method called with the configuration of this class
        """
        pass

    @classmethod
    def get_example_resource(cls):
        """
        Generate an example of the resources managed by this manager
        Computed by the `example` of each resource field in
        :attr:`Manager.resource_fields`
        """
        return cls._resource_fields.get_example_resource()

    @classmethod
    def detect(cls):
        """
        Auto detection function.
        This function is called by napixd to check if the manager is needed

        By default, this methods return False for builtin managers
        or returns the value of :attr:`auto_load`
        """
        return (not cls.__module__.startswith('napixd.managers') and
                cls.auto_load)

    def serialize(self, value):
        return self._resource_fields.serialize(value)

    def unserialize(self, value):
        return self._resource_fields.unserialize(value)

    def validate_id(self, id_):
        """
        Check that the id given as an argument is a valid ID

        The id is always a string extracted from the url.

        If the id is not valid, raises a :exc:`napixd.exceptions.ValidationError`.
        If necessary, modify the id and return it.
        this method MUST return the ID even if it wasn't modified.

        Example:

        >>> class IntID(Manager):
        ...     def validate_id(self, id_):
        ...         "The id must be an int"
        ...         try:
        ...             return int(id_)
        ...         except ValueError:
        ...             raise ValidationError

        >>> class MinLength(Manager):
        ...     def validate_id(self,id_):
        ...         "The id must be a string containing at least 3 characters"
        ...         if len(id_) < 3:
        ...             raise ValidationError
        ...         #always return the id
        ...         return id_

        By default, this method checks if the id is not an empty string.
        """
        if id_ == '':
            raise ValidationError('A non empty ID is expected')
        return id_

    def validate_resource(self, resource_dict, origin=None):
        """
        Validates a resource_dict (which can be directly a dict or an object
        emulating a dict) by checking that every mandatory field specified in
        :attr:`resource_fields` is defined.

        If the current object implement :meth:`validate_resource_FIELDNAME`
        method, it'll be called with the value of resource_dict[FIELDNAME] as
        parameters.  It shoud raise a :exc:`napixd.exceptions.ValidationError`
        if the data isn't valid, else it must return a valid value

        Returns a resource_dict.
        """
        return resource_dict

    def validate(self, resource_dict, original=None):
        """
        Validates the resource.

        First, it calls the :class:`napixd.managers.resource_fields.ResourceFieldsDescriptor.validate`,
        then it calls :meth:`validate_resource`. If there is an *original*
        object given, a :class:`napixd.managers.changeset.DiffDict` is
        computed with the original and proposed object.

        """
        # Create a new dict to populate with validated data
        if original is not None:
            serialized = self.serialize(original)
            resource_dict = self._resource_fields.validate(
                resource_dict, serialized)
            resource_dict = DiffDict(serialized, resource_dict)
        else:
            resource_dict = self._resource_fields.validate(resource_dict, None)
        return self.validate_resource(resource_dict, original)


class ManagerInterface(object):

    """
    HTTP calls map

    This interface MUST NOT be inherited by the subclasses.

    The managers MAY not implement all the methods below.
    The method not implemented will be answered by a
    405 METHOD NOT ALLOWED response with the list of methods auhorized
    computed according to the existing methods.

    If a attribute or a method of the manager has one of those methods name,
    the functionnality will be considered being implemented.

    The manager MUST NOT define a method with a raise NotImplementedError
    to mean that the method is not supported.
    """

    def delete_resource(self, resource):
        """
        Delete a managed ressource.

        Eg :
        DEL /something/[...]/mymanager/42
        will be translated to :
        mymanager.delete_resource('42')

        """
        raise NotImplementedError

    def create_resource(self, resource_dict):
        """
        Create a new managed ressource.

        resource_dict is a dict populated with the data sent by the user after
        they have been cleanned

        This method MUST return the id of the resource created

        Eg:
        POST /something/[...]/mymanager/ with resource_dict { 'toto': 1 }
        will be translated to :
        mymanager.create_resource({ 'toto': 1})
        """
        raise NotImplementedError

    def get_resource(self, resource_id):
        """
        Get the ressource object corresponding to resource_id.

        This object must be a dict or emulate it, as the nAPIxd will convert
        this dict to a json object to build his response.

        Eg: GET /somehting/[...]/mymanager/42
        calls
        mymanager.get_resource(self, '42')

        """
        raise NotImplementedError

    def modify_resource(self, resource, changes):
        """
        Modify the ressource designed by resource_id by updating it
        with resource_dict defined values.

        Eg: PUT /something/[...]/mymanager/42
        will be translated to :
        mymanager.modify_resource('42', { 'toto': 4242 })

        The method MAY return an id.
        If the ID changes the response will notify the client.
        """
        raise NotImplementedError

    def list_resource(self):
        """
        Return the ids list of all managed resource.
        It should return a list of string representing each id
        of the collection.

        Eg: GET /something/[...]/mymanager/
        will be translated to
        mymanager.list_resource()
        """
        raise NotImplementedError

    def list_resource_filter(self, filters):
        """
        Return the list of ids of all managed resources matching the *filters*.

        *filters* is a mapping of filters to apply to this request
        It behaves like a dict with an additional :meth:`getall(key)` method
        that returns a list of all the values matching the given **key**.
        """
        raise NotImplementedError

    def get_all_resources(self):
        """
        Return the tuple of (id, resource) for all the managed resources.

        See :meth:`list_resource` and :meth:`get_resource`.
        """

    def get_all_resources_filter(self, filters):
        """
        Return the tuple of (id, resource) of all managed resources
        matching the *filters*.

        See :meth:`list_resource_filter` and :meth:`get_all_resources`
        """
        raise NotImplementedError
