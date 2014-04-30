#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = [
    'PermissionDenied',
    'ValidationError',
    'NotFound',
    'Duplicate',
    'ImproperlyConfigured',
    'RemoteError',
    'InternalRequestFailed',
]

import collections


try:
    from napix.exception import HTTPError as RemoteError
except ImportError:
    class RemoteError(Exception):
        """
        Error caused by a request in another Napix Server.
        """
        def __init__(self, request, cause, response):
            self.request = request
            self.remote_error = cause
            self.response = response

        def __str__(self):
            return str(self.remote_error)


class InternalRequestFailed(Exception):
    """
    Thrown when a internal request to a sub-manager, a service or a resource fails.
    """
    pass


class PermissionDenied(Exception):

    """
    Thrown when a user try to do something he is not allowed
    """
    pass


class ValidationError(collections.Mapping, Exception):

    """
    Thrown when a validation fails on a element submitted by the user
    """

    def __init__(self, error=''):
        if isinstance(error, list):
            errors = error
            error = {}
            for validation_error in errors:
                error.update(validation_error)
        elif isinstance(error, Exception):
            error = unicode(error)

        if isinstance(error, dict):
            self.errors = error
            error = ''
        else:
            self.errors = {'_napix_': error}

        super(ValidationError, self).__init__(error)

    def __eq__(self, other):
        return (isinstance(other, ValidationError) and
                self.errors == other.errors)

    def __repr__(self):
        return 'ValidationError({0})'.format(self.errors)

    def __iter__(self):
        return iter(self.errors)

    def __getitem__(self, item):
        return self.errors[item]

    def __len__(self):
        return len(self.errors)


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


class ImproperlyConfigured(Exception):

    """
    When a piece of code is not as expected
    """
    pass
