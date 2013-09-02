#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = [ 'PermissionDenied', 'ValidationError', 'NotFound', 'Duplicate', 'ImproperlyConfigured' ]


class PermissionDenied(Exception):
    """
    Thrown when a user try to do something he is not allowed
    """
    pass

class ValidationError(Exception):
    """
    Thrown when a validation fails on a element submitted by the user
    """
    def __init__( self, error=''):
        if isinstance( error, ValidationError):
            error = dict( error)
        elif isinstance( error, Exception):
            error = unicode( error)

        if isinstance( error, dict):
            self.errors = error
            error = ''
        else:
            self.errors = { '_napix_' : error }

        super( ValidationError, self).__init__( error )

    def __iter__(self):
        return iter( self.errors.items())




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


class ImproperlyConfigured( Exception):
    """
    When a piece of code is not as expected
    """
    pass

