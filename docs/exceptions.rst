
.. module:: exceptions

Exceptions defined by Napix
===========================

.. exception:: ValidationError

    Thrown when a validation fails on a element submitted by the user

.. exception:: NotFound

    Exception that means that the resource queried is not available.
    It should be thrown with the asked id.

.. exception:: Duplicate

    When a new record was being created and another record was already present at that ID.
