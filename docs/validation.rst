.. _validation:

.. currentmodule:: napixd.managers.base

=======================
Validating user's input
=======================

Napix managers take input from the users.
This input have to be validated in order to check consistency
of the user's input and to avoid harmful or dangerous values.

Inputs to be validated
======================

The validation mechanisms of Napix are used in:

* The id given to :meth:`~ManagerInterface.get_resource`
* The :mod:`actions<napixd.managers.actions>`
* The :meth:`creation<ManagerInterface.create_resource>`
* The :meth:`modification<ManagerInterface.modify_resource>`


Validation protocol
-------------------

The user's input of Napix modules should be checked by writing validation methods,
or using generic :mod:`~napixd.managers.validators`.
They take the proposed user input as an entry and return the correct data.

URL token validation
====================

:meth:`~Manager.validate_id` is the method which checks the url tokens
(part **resource_id** of /manager/**resource_id**).
It takes the proposed user input and return the correct user input.
If the user input is not suitable,
it raises a :exc:`napixd.exceptions.ValidationError` with a message
describing the kind of error that has been done.

.. code-block:: python

    class MyFileManager(Manager):
        resource_fields = {
            'content': {
                'example': ''
            }
        }

        def get_manager(self, id):
            with open(os.path.join(ROOT, id) as handle:
                content = handle.read()
            return {
                'content': content
            }

This code sample has a vulnerability if an id containg slashes is given.
The validation method :meth:`~Manager.validate_id` can check the id
to protect the :meth:`~ManagerInterface.get_resource` method.

.. code-block:: python

    class MyFileManager(Manager):
        resource_fields = {
            'content': {
                'example': ''
            }
        }

        def get_manager(self, id):
            with open(os.path.join(ROOT, id) as handle:
                content = handle.read()
            return {
                'content': content
            }

        def validate_id(self, input):
            if '/' in input:
                raise ValidationError('id must not contain /')
            return input

The correct value, with eventual type cast or other modifications is
returned by :meth:`Manager.validate_id`.
Even if the value is not changed, the method must return the value.


Request body validation
=======================

The input for resource dicts is validated by the :class:`Manager`
in its method :meth:`Manager.validate`.
This method implements a generic validation mechanism and delegate
user validations in an overriadable method :meth:`Manager.validate_resource`.

Generic validation protocol
---------------------------

.. currentmodule:: napixd.managers.resource_fields

First, each field is individually validated.
The :meth:`ResourceFieldsDescriptor.validate`
is called that in turn calls the
:meth:`ResourceField.validate` of each field.

The validation of each field is made by:

* The validators :attr:`ResourceField.validators` are called in the order of the list.
* The :meth:`validate_resource_FIELDNAME` of the :class:`napixd.managers.base.Manager` if it exists.

.. currentmodule:: napixd.managers.base

Once each field is validated, the whole resource is validated.
The method :meth:`Manager.validate` is called.
The origin parameter depends on the type of request made: creation (POST) or modification (PUT).

The value returned by :meth:`~Manager.validate` is fed to :meth:`ManagerInterface.modify_resource`
or :meth:`ManagerInterface.create_resource`.

The user specific validation should be added to the :meth:`validate_resource`.
This method should return the validated dict.

Creation
________


For creation requests, the *origin* parameter for :meth:`Manager.validate` and
:meth:`Manager.validate_resource` is None.
The resource_dict is a :class:`dict` of the fields that are not
:attr:`~napixd.managers.resource_fields.ResourceField.computed`

Modifications
_____________

When modifying of an existing resource, the *origin* paramater of the :meth:`Manager.validate_resource`
is the resource as returned by :meth:`~ManagerInterface.get_resource`.
The resource is serialized by :meth:`Manager.serialize` and
the fields not :attr:`~napixd.managers.resource_fields.ResourceField.editable`
or :attr:`~napixd.managers.resource_fields.ResourceField.computed`.
are copied from the serialized resource.
