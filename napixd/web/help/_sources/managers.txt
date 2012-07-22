
.. module:: managers

Manager
=======

The Manager class is the base class for all managers.

Manager :
    - manages a set of resources
    - does it by defining create/delete/modify methods that act on those resources
Ressource :
    - MUST be a dict (or an emulation thereof) that hold a set of properties.
      The resource may be an arbitrary object, but the manager MUST then implements a serialize method
      that convert this object to a dict.
    - They MAY have actions

Manager are created by the corresponding resource

.. class:: Manager

   Base class of the managers

    Managers are objects created to serve requests on a resource for its sub resources
    example::

       GET /physics/constants/c

    A manager is created of the resource *physics*, this resource is asked for its child *constants*,
    a manager for this resource *constant* is created, and this manager is asked for its child *c*.
    The resource got is serialized and sent back to the user

    Managers cycle of life MAY contains multiple request, that MAY be executed simultaneously.

    The cycle of life is :

    - Class creation
    - Insertion into the application inside the root manager or through a parent manager
    - An instance is generated for a resource
       * start_request is called
       * the appropriate method to respond to the request is called (get_resource, create_resource, etc)
       * end_request is called

    examples:

    .. code-block:: python

        class FirstManager(Manager):
            managed_class = SecondManager

        class SecondManager(Manager):
            def list_resource(self):
                return {}

        #GET /first/second/third
        second_resource = FirstManager().get_resource('second') #/first
        second_manager = SecondManager(second_resource)  # [..]/second
        return second_manager.get_resource('third')  # [..]/third

    If it's a tuple or a list of classes, the children have multiple subressource managers attached.
    The class in wich the children is wrapped depends on the url path
    example

    .. code-block:: python

        class Main(Manager):
             managed_class = [ManagerA,ManagerB]
        class ManagerA(Manager):
             pass
        class ManagerB(Manager):
             pass

        #GET /main/1
        Main().get_resource(1)

        #GET /main/1/
        [ 'A', 'B' ]

        #GET /main/1/A/
        ManagerA(Main().get_resource(1)).list_resource()

        #GET /main/1/B/
        ManagerB(Main().get_resource(1)).list_resource()

        #GET /main/1/B/3
        ManagerB(Main().get_resource(1)).get_resource(3)

    If it's not set, the manager does not have sub resources::

        #GET /first/second/third/
        404 NOT FOUND

        #GET /first/second/third/fourth
        404 NOT FOUND

    The resources may contains some fields that are not in the class' resource_fields.
    When the resource are serialized to be send in json,
    only the fields in resource_fields are extracted.

    This behavior may be usefull to pass privates values to the next managers.
    exemple

    .. code-block:: python

            class SectionManager(Manager):
                """
                Manages each of the section of a configuration file
                """
                def list_resource(self):
                    return self.parent['parser'].get_sections()

            class File(Manager):
                """
                Manages a list of configuration files inside /etc
                """
                 managed_class = SectionManager
                 resource_fields = {
                    'path': {
                        'description' : 'file path'
                        }
                    }
                 def get_resource(self,id):
                     return {'parser':Parser('/etc/'+id),'path':'/etc'+id}

            GET /file/file1
            { "path" : "/etc/file1" }
            #No parser field sent

            GET /file/file1/
            [ "section1" , "section2"]
            #Parser was passed to list_resource through parent

    .. attribute:: parent

        The resource that spawned this manager in the context of a request on a sub manager.

        For the first level managers, it is None.


    .. attribute:: managed_class

        A class, or an array of classes that will manager a sub-collections.
        The classes can be replaced by a string being, the name of another class
        declared in the file or the dotted python path to another manager.

        If it is a single value, the children resources are directly connected to the parent manager.

        .. code-block:: python

            class FirstManager( Manager):
                @classmethod
                def get_name(cls):
                    return 'first'
                managed_class = 'ChildManager'

            class SecondManager( Manager):
                @classmethod
                def get_name(cls):
                    return 'second'
                managed_class = [ 'ChildManager' ]

            class ChildManager( Manager ):
                @classmethod
                def get_name(cls):
                    return 'children'
                pass

        .. code-block:: none

            GET /first/id_parent/
            list of children resources

            GET /first/id_parent/id_child
            { child resource }

            GET /second/id_parent/
            [ 'other' ]

            GET /second/id_parent/other/
            list of children resources

            GET /second/id_parent/children/id_child
            { other_resource }

    .. classmethod:: set_managed_classes( managed_classes )

        Set the managed classes of the manager.
        The orginal :attr:`managed_class` attribute is left untouched.

        The managed_class parameter must be a list of class objects.

        This method is called by the loader after it resolved the string references.

    .. classmethod:: get_managed_classes

        return the list of managed classes.
        It always returns a list even if the managed is directly plugged.

        If :attr:`managed_class` contains a list or one direct references to class objects,
        it is not needed to call :meth:`set_managed_classes`,
        else string references have to be resolved.

        .. code-block:: python

            class FooManager( Manager ):
                managed_class = 'BarManager'

            FooManager.get_managed_classes()
            #warning: Manager foomanager has not been set up.
            #should have called set_managed_classes
            [ 'BarManager' ]

            class MyManager( Manager ):
                managed_class = MyDirectReference

            FooManager.get_managed_classes()
            #ok
            [ MyDirectReference ]

    .. classmethod:: direct_plug

        Return how the managed classes are plugged to this manager.
        If there isn't any managed_class, it returns None.
        If there is a managed class directly declared into the manager, it returns true,
        else if the class are declared in an iterable it is True.::

            managed_class = [ 'SubManager' ]
            direct_plug == False

            managed_class = 'SubManager'
            direct_plug == True

            managed_class = None
            direct_plug == None


    .. method:: __init__( parent )

        intialize the Manager with the parent resource creating it

        .. code-block:: python

            class FirstManager(Manager):
                 managed_class = SecondManager

            class SecondManager(Manager):
                 def list_resource(self):
                     return {}

            #GET /first/second/
            SecondManager(FirstManager.get_resource('second')).list_resource()


    .. classmethod::  detect() -> Boolean

        Auto detection function.
        This function is called by napixd to check if the manager is needed,
        when it is loaded by autodetection.

        .. code-block:: python

            import platform

            @classmethod
            def detect(cls):
                #Activate the manager only if the host is Linux
                return platform.platform() == 'Linux'

    .. method::  configure(conf)

        Method called with the configuration of this class

    .. method::  is_up_to_date()

        Method to check if the data contained are fresh.
        If it's not the manager is recreated

    .. method::  start_request(request)

        Method called at the beginning of the request.

        .. warning::

            It can be called after :meth:`get_resource` when get_resource is called for a sub manager.

    .. method:: start_managed_request( request, resource_id, resource)

        Method called when the manager executes its :meth:`get_resource`
        for a request on a submanager.

        ``resource`` and ``resource_id`` are the resource and id of the resource generated by this manager.

    .. method:: end_managed_request( request, resource_id, resource)

        like :meth:`start_managed_request`, but called at the end of the request, but called at the end of the request.

    .. method::  end_request(request)

        This method is called after a request involving this manager directly or calling a submanager.

    .. method:: serialize( resource ) -> resource_dict

        Serialize the resource before it is send to the client.

        By default, it takes a dict and return another dict containing only the keys declared in
        :attr:`resource_fields`.

        It is called only on GET request on this resource, not for the request on sub managers.

Auto documentation
------------------

.. class:: Manager

    .. attribute:: name

        The name of the class, None by default.
        Always use :meth:`get_name` if you need to know the name of a manager.

    .. classmethod::  get_name() -> name

        Returns the name of the manager.
        If :attr:`name` is not defined, it's the class name in lower case.

    .. method::  get_example_resource() -> resource_dict

        Generate an example of the resources managed by this manager
        Computed by the *example* of each resource field in :attr:`resource_fields`


    .. attribute:: resource_fields

        List of the fields publicly available with their properties

        Subclasses of this class MUST define their own list of fields
        in the class attribute resource_fields.

        This attribute is a dict where the keys are the fields names and the values are
        the descriptions of those fields

        Properties includes:

            * optional : if the value is optional
            * example : used for documentation and the example resource
            * description : describe the use of the resource
            * computed : This field is computed by the service and the user CAN NOT force it

        example:

        .. code-block:: python

            class User(Manager):
                resource_fields = {
                    'username':{'description':'POSIX username of the system account', 'example':'dritchie'},
                    'uid':{'description':'Unique identifier, will be generated if not given','optional':True},
                    'gecos':{'description':'Comment on the user name',example:'Dennis M. Ritchie'}
                    }

.. _validation:

Validation
----------

.. class:: Manager

    The validation methods of the Manager class take the proposed user input and either return the correct value even if unchanged
    or raise a :exc:`ValidationError`.

    It may change the type of the variable,
    for example to convert number to strings to integer values,
    to query integer indexed values in a list.


    .. method::  validate_id(id) -> id

        Check that the id given as an argument is a valid ID

        The id is always a string extracted from the url.

        If the id is not valid, raises a :exc:`ValidationError`.
        If necessary, modify the id
        this method MUST return the ID even if it wasn't modified.

        This method shoud not check if the id correspond to an existing value.
        It shoud just verify that the id does not contains anything that can harm the next methods,
        `delete_resource`, `get_resource` or `modify_resource`.
        Else, it could lead to 400 errors instead of 404 errors.

        example:

        If the id must be an int

        .. code-block:: python

             class IntID(Manager):
                 def validate_id(self,id_):
                     try:
                         return int(id_)
                     except ValueError:
                         raise ValidationError

        If the id must be a string containing at least 3 charcters

        .. code-block:: python

            class MinLength(Manager):
                 def validate_id(self,id_):
                     if len(id_) < 3:
                         raise ValidationError
                     #always return the id
                     return id_

        By default, this method checks if the id is not an empty string

    .. method::  validate_resource_FIELDNAME( value )

        If a Manager defines a field `x` and a method `validate_resource_x`,
        this method will be used to validate this field.

        Like :meth:`validate_id`, it must return the correct value, even if it was not changed
        or throw a :exc:`ValidationError` if the value is incorrect.


    .. method:: validate_resource( resource_dict) -> resource_dict

        Placeholder method of the managers for the validation of the whole resource_dict
        This method can change, add or remove fields from the resource_dict.
        It must return the valid resource even if it is the same as resource_dict,
        or raise a :exc:`ValidationError`.

        .. code-block:: python

            class CNAMEManager( Manager):
                """ Manages the aliases """

                def validate_resource( self, resource_dict):
                    #avoids a redirection on itself
                    if resource_dict['name'] == resource_dict['target']:
                        raise ValidationError, '`name` and `target` must be different'
                    return resource_dict

    .. method:: validate( resource_dict ) -> resource_dict

        Validate a resource_dict by checking that every mandatory field specified in self.resource_fields is defined.

        First, if the current object implement :meth:`validate_resource_FIELDNAME` method, it'll be called with
        the value of resource_dict[FIELDNAME] as parameter.

        Then it will call validate_resource with the dict which has its fields cleaned


Collection and resources methods
--------------------------------

.. class:: Manager

    The :class:`Manager` class does not implements any of these.

    The Manager subclasses *MAY* implement all or only a part of the methods below.

    The not implemented methods will be answered by a 405 METHOD NOT ALLOWED response
    with the list of the authorized methods computed from to the existing methods.

    If a Manager subclass implements a method or define an attribute with one of those names,
    the corresponding feature will be considered being implemented.

    The manager MUST NOT define a method with a raise NotImplementedError
    to mean that the method is not supported.


    All the **resource_id** and **resource_dict** given to the following methods have been cleaned with
    :meth:`validate_id` and :meth:`validate_resource` respectively.


    .. method::  delete_resource(resource_id)

        Delete a managed ressource.

        .. code-block:: python

            #DELETE /something/[...]/mymanager/42
            mymanager.delete_resource('42')

    .. method::  create_resource( resource_dict) -> id

        Create a new managed ressource.

        resource_dict is a dict populated with the data sent by the user after they have been cleaned.

        This method MUST return the id of the resource created

        .. code-block:: python

            #POST /something/[...]/mymanager/ with resource_dict { 'toto': 1 }
            mymanager.create_resource({ 'toto': 1})


    .. method::  get_resource(resource_id) -> resource

        Get the ressource object corresponding to resource_id.

        This object must be a dict or emulate it, as Napix will convert this dict
        to a json object to build his response.

        If an object define keys that are not in the :attr:`resource_fields`,
        they will be stripped.

        .. code-block:: python

            #GET /somehting/[...]/mymanager/42
            mymanager.get_resource(self, '42')


    .. method::  modify_resource(resource_id,resource_dict)

        Modify the ressource designed by resource_id by updating it with resource_dict
        defined values.

        If modify_resource is not defined, it's emulated by calling delete/create sequentially.

        .. code-block:: python

            #PUT /something/[...]/mymanager/42
            mymanager.modify_resource('42', { 'toto': 4242 })


    .. method::  list_resource() -> list

        Return the ids list of all managed resource. The result can be of 2 form : either a direct list
        of string, representing each id, or a list of dict, defining at least '_id' and '_desc' as key.

        .. code-block:: python

            #GET /something/[...]/mymanager/
            mymanager.list_resource_id()

        After processing, the Napix daemon will always convert the list in a list of dict, and add
        the _uri key with appropriate value (based on baseurl + _id).

