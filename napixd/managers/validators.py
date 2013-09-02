#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from napixd.exceptions import ValidationError


class MatchRegexp(object):
    def __init__(self, source, default=None, error=None, docstring=None):
        if not docstring:
            docstring = 'Field have to match regex {0}'.format(source)
        if not error:
            error = 'Value {value} have to match {regex}'
        self.error = error

        self.__help__ = docstring
        self.default = default
        self.regex = re.compile(source)

    def __call__(self, value):
        if self.default is not None and value is None:
            return self.default
        if not self.regex.match(value):
            raise ValidationError(self.error.format(
                value=value, regex=self.regex))
        return value
