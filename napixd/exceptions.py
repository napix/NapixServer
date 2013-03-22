#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = [ 'PermissionDenied', 'ValidationError', 'NotFound', 'Duplicate' ]


class PermissionDenied(Exception):
    """
    Thrown when a user try to do something he is not allowed
    """
    pass

class ValidationError(Exception):
    """
    Thrown when a validation fails on a element submitted by the user
    """
    pass

class NotFound(Exception):
    """
    Exception that means that the resource queried is not available.
    It should be thrown with the asked id.
    """
    pass

class Duplicate(Exception):
    """
    When a new record was being created and another record was already present at that ID.
    """
    pass
