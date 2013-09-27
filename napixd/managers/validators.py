#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
This module defines generic validators to use
with :attr:`napixd.managers.resource_fields.ResourceField.validators`.
"""

import re
from napixd.exceptions import ValidationError


def not_empty(value):
    """
    Checks that the *value* is not an empty string.
    """
    if value == '':
        raise ValidationError('This should not be empty')
    return value


class MatchRegexp(object):
    """
    Checks that the input matches the *source* regexp

    If not, a :exc:`napixd.exceptions.ValidationError` is raised
    with *error* text.
    Error is formatted with :meth:`str.format` and two keyword:
    **value**: the value that failed the validation and
    **regex**: the regexp that it should match.

    The *docstring* parameter defines the help of the validator,
    it is used for introspection.
    """

    def __init__(self, source, default=None, error=None, docstring=None):
        if not docstring:
            docstring = 'Field have to match regex {0}'.format(source)
        if not error:
            error = 'Value {value} have to match {regex.pattern}'
        self.error = error

        self.__doc__ = docstring
        self.default = default
        self.regex = re.compile(source)

    def __call__(self, value):
        if self.default is not None and value is None:
            return self.default
        if not self.regex.match(value):
            raise ValidationError(self.error.format(
                value=value, regex=self.regex))
        return value
