#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
This module defines generic validators to use
with :attr:`napixd.managers.resource_fields.ResourceField.validators`.
"""

import re
import collections

from napixd.exceptions import ValidationError


class StringValidator(object):
    """
    Base string validator.

    It strips the trailing whitespace if strip is ``True``. It rejects string
    containing a new line character if multiline is ``False``. It rejects empty
    strings if empty is ``False``.

    docstring is either a string that is used as a the :func:`help`, or a list
    of strings concatenated to the default :func:`help`.
    """
    def __init__(self, strip=True, multiline=False, empty=False, docstring=None):
        self._strip = strip
        self._multi = multiline
        self._empty = empty
        doc = []
        if self._strip:
            doc.append(u'Trailing whitespace is ignored.')
        if not self._multi:
            doc.append(u'Only single line string.')
        if not self._empty:
            doc.append(u'No empty strings.')
        if isinstance(docstring, basestring):
            self.__doc__ = docstring
        else:
            if docstring:
                doc.extend(docstring)
            self.__doc__ = u'\n'.join(doc)

    def __call__(self, value):
        if self._strip:
            value = value.strip()
        if not self._multi and ('\n' in value or '\r' in value):
            raise ValidationError(u'String have to be a single line')
        if value == '':
            raise ValidationError('This should not be empty')
        return value

strip = StringValidator(strip=True, multiline=True, empty=True)
not_empty = StringValidator(strip=False, multiline=True, empty=False)
single_lined = StringValidator(strip=False, multiline=False, empty=True)


class MatchRegexp(StringValidator):
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

    def __init__(self, source, error=None, docstring=None, **kw):
        if not docstring:
            docstring = ['Field have to match regex {0}'.format(source)]
        super(MatchRegexp, self).__init__(docstring=docstring, **kw)

        if not error:
            error = 'Value {value} have to match {regex.pattern}'
        self.error = error
        self.regex = re.compile(source)

    def __call__(self, value):
        value = super(MatchRegexp, self).__call__(value)
        if not self.regex.match(value):
            raise ValidationError(self.error.format(
                value=value, regex=self.regex))
        return value
