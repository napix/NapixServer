
.. currentmodule:: managers.default

.. highlight:: python

.. _high_level:

=========================
Howto write Napix modules
=========================

Considering that you already read :ref:`The first steps guide<first_step>`,
this page deals with more advanced topics.

The example of this page is an host file manager.
This manager get the hosts file, extracts from each line the IP and the hostnames.
Even though it may be a questionable choice,
the id is the number of the line in the file as it allow to keep the comments.

Writing the module
==================

Loading the file
^^^^^^^^^^^^^^^^

In order to write this module you have to write a ``manager`` and install it in the Napix server.
A Napix module may be in every place that is accessible in the python path.
Napix automatically tries to load every module in :file:`{HOME}/auto`.

The napixd daemon display its home in the log and the console.::

    (napix)$ bin/napixd
    ...
    Found napixd home at /home/user/NapixServer
    ...

For more details about the loading of modules inside Napix, see the :ref:`loading page<auto-loading>`

Napix Class
^^^^^^^^^^^

The base class behind every collection is :class:`managers.Manager`.
It defines how the collection find, modify and make operations on its resources.

For convenience, some subclasses of :class:`~managers.Manager` are defined in
:mod:`managers.default` that ease the creation of a manager at the expense of higher consumption
of CPU and RAM.

:class:`DictManager` is the base class of the manager we will be writing.
It's a subclass of :class:`managers.Manager` witch implements higher level construct:
with this implementation, it is just needed to make a dict of resource by ID from a persisted data source and to save it back.

For the hosts example, we will write an implementation of this class.
We add a docstring for our class.
It will be used by Napix to document the service.

The file will be :file:`{HOME}/auto/hostmanager.py` in order to benefits from auto-loading.

Writing the meta-datas
^^^^^^^^^^^^^^^^^^^^^^

First you need to write the :attr:`~managers.Manager.resource_fields` attribute that describes the resource.

For our example, we will use two fields:
    * a string for the IP address
    * an array of hostnames related to this IP.

For each of our fields, we add a key in the :attr:`~managers.Manager.resource_fields`
dictionary containing another dict describing the field.
We add a description and an example.

.. literalinclude:: /samples/sample1.py
    :lines: 4-20

.. note::

    The example key is not a default value, it's used when the user requests a
    :meth:`~managers.Manager.get_example_resource`
    as a template to create a new one and for documentation purposes.

Loading the resources
^^^^^^^^^^^^^^^^^^^^^

In order to get the resources, you have to define the :meth:`ReadOnlyDictManager.load` method.
This method must return a dictionary of the resources indexed by their keys.


For the manager we are writing, we will use the line number as an index.
Since we install our manager in the root of the service,
we will ignore the parent parameter in the load and save methods.


.. literalinclude:: /samples/sample1.py
    :pyobject: HostManager.load

Creating resources
^^^^^^^^^^^^^^^^^^

At this point, the resources can be listed, got, deleted and modified.
In order to add new resources, the manager must be able to generate the corresponding ID
of a new resources.
You have to write the method :meth:`DictManager.generate_new_id` that will return the id of the new resource
knowing its dictionary.

You may choose to get a UUID, a sequence number, a value from the dictionary, etc,
as long as this id will allow to query the same object in the future, and will be persisted.

In the manager we're writing, we are using the line number as identifier,
so we will use the size of the file we already have.

.. literalinclude:: /samples/sample1.py
    :pyobject: HostManager.generate_new_id

Persisting the resources
^^^^^^^^^^^^^^^^^^^^^^^^

The data can now be queried, modified, removed, added.
In order to persist the modifications in the time, you will have to write a save method that will persist
the data you modified.
At every call of persist, you will save all the resources of the manager,
not only those which have been modified.


For the files manager, we will write the hosts files.
As with the load method, we don't need the parent parameter, so it will be ignored.

.. literalinclude:: /samples/sample1.py
    :pyobject: HostManager.save

Resulting file
^^^^^^^^^^^^^^

You can download the :download:`/samples/sample1.py` file.

Validation
==========

The user's input of our Napix modules should be checked by writing validation methods.
They take the proposed user input as an entry and return the correct data.
There's two kind of input to validate or transform:
* the input given by the user when he tries to create or transform the data of the resources
* the id that the user wants to query, for example GET /manager/**resource_id1**.

URL token validation
^^^^^^^^^^^^^^^^^^^^

:meth:`~managers.Manager.validate_id` is the method which checks the url tokens
(part **resource_id** of /manager/**resource_id1**).
It takes the proposed user input and return the correct user input or, if it's wrong,
raises a :exc:`~ValidationError` with a message describing the kind of error that has been done.

In our example, we may want to keep the ids as integers

.. warning:: It's not the time to check for the existence

    This method should just check that the ID may be a valid ID for the rest of the methods.
    It's not the methods in which you should check that a value already exists or not.

.. literalinclude:: /samples/sample1_validation.py
    :pyobject: HostManager.validate_id

.. note::

    In order to make this snippet working, you have to remove the str in `load`, `save` and `generate_new_id`

Request body validation
^^^^^^^^^^^^^^^^^^^^^^^

There is two places where the strings are validated.
First in the :meth:`validate_resource_*<managers.Manager.validate_resource_FIELDNAME>` methods that check each field individually.
Then in the :meth:`~managers.Manager.validate_resource` that validate the whole data dictionary.
It may be used to convert integers to strings, clean a string, ensure consistency etc.

Those methods get the object (the whole dict or each field) to validate by argument and must return the correct value.
When a value is incorrect, the method throws a :exc:`~ValidationError`
with a string describing the kind of error the user did.

With the HostManager, we may want to check that users are sending an array of strings as the hostnames attribute
and a valid and clean IP address for the ip attribute.

.. literalinclude:: /samples/sample1_validation.py
    :pyobject: HostManager.validate_resource_hostnames

.. literalinclude:: /samples/sample1_validation.py
    :pyobject: HostManager.validate_resource_ip

Resulting file
^^^^^^^^^^^^^^

You can download the :download:`/samples/sample1_validation.py` file.

Deployment and configuration
============================

Install into Napix
^^^^^^^^^^^^^^^^^^

To add the new module to the Napix server, you need to add the path to its class in
the configuration file: :file:`conf/settings.json`.


The key ``Napix.managers`` hold a dictionary of the manually activated modules.
The key of this dict is the alias of the module, and the value is the path to the module.


Mutliple aliases may refer to the same class, then it will launch multiples instances of the manager.
It may be useful for example to load multiple hosts managers for different hosts files.

Configuration
^^^^^^^^^^^^^

The Napix managers have a method configure that does nothing by default but is called
with the configuration of the module if any.


You may override the configure method of a Napix manager :meth:`~managers.Manager.configure`.
This classmethod takes an argument which is the configuration found in the settings file.

For the HostManager we may add a configuration option to set another hosts file path.

The configure method get the dictionary that we set in :file:`conf/settings.json`.

Test case
=========

Testing the module is quite easy.
You instantiate a manager with its parent resource if it has one, then you can test the behavior
with of the load and save methods.

For example the tests of the HostManager :download:`/samples/sample1_tests.py`.

