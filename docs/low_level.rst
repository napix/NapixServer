
.. highlight:: python
.. currentmodule:: napixd.managers.base

=======================================================
Howto write a Napix module with the low level interface
=======================================================

The :ref:`Napix high level howto<high_level>` teaches about writing and setting up a Napix module that get and serialise a list of resources.
When the list become too big or is slow or difficult to save, you may choose to get the resources one by one
using the low-level interface.

The base manager of Napix does not require any method to be implemented.
It proposes five methods that correspond to the HTTP actions:

Each method implemented will enable the HTTP call in the documentation and metadata of the manager.
None is required. You may write a manager that can get a resource, modify it
but neither delete, nor create, nor list them.

For this howto, we will take the example of a LVM volume manager.

First steps
===========

Napix Class
-----------

The class we will be using is the base manager of Napix.
The doctstring is used by napix to document the service.


The next step is to fill the :attr:`~Manager.resource_fields` attribute with the fields
we will export in our service.

.. literalinclude:: /samples/sample2.py
    :lines: 9-12

The service will export the name of the logical volume, its size and the group it belongs to.

.. literalinclude:: /samples/sample2.py
    :lines: 13-26


List the resources
------------------

The :meth:`~Manager.list_resource` method return the list of the possible ID.

We choose to use the uuid of the LVM volume as the identifier of the resource.

.. literalinclude:: /samples/sample2.py
    :lines: 46-59

Get a resource
--------------

The :meth:`~Manager.get_resource` method is called with the desired id.
This id has already been cleaned by the :meth:`~Manager.validate_id` method.
If there is nothing corresponding to the id, the method must raise a :exc:`NotFound` exception.

.. literalinclude:: /samples/sample2.py
    :lines: 28-39,61-69

Validate the input
------------------

The modify and create method get a data_dict argument.
It is cleaned by the validate_resource for the whole resource and
each field individually by the the :meth:`validate_resource_*<Manager.validate_resource_FIELDNAME>` methods.

The arguments given to the modify and create must be cleaned,
to check that the value have the right type and do not contain harmful values,
such as '..' in a filename, quotes, or \n, etc.

More detail on the validation process :ref:`here<validation>`.

We write these validation method in order to ensure that the next methods we will write run safely.

.. literalinclude:: /samples/sample2.py
    :lines: 41-44,71-90

Create a resource
-----------------

The :meth:`~Manager.create_resource` method takes the cleaned data_dict as argument and must return the id of the object it created.
If there is a conflict with an existing resource, it may throw a :exc:`Duplicate` exception.

.. literalinclude:: /samples/sample2.py
    :pyobject: LVMManager.create_resource

Delete a resource
-----------------

The :meth:`~Manager.delete_resource` get the id of the resource to delete.

.. literalinclude:: /samples/sample2.py
    :pyobject: LVMManager.delete_resource

Resulting file
==============

You can download the resulting file at :download:`/samples/sample2.py`.
