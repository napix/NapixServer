#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.exceptions import ValidationError, ImproperlyConfigured


class Map(object):
    def __init__(self, *validators):
        if not validators:
            raise ImproperlyConfigured('Map requires at least one validator')
        if not all(callable(v) for v in validators):
            raise ImproperlyConfigured('Map requires a list of validtors')

        self.validators = list(validators)

    def __call__(self, value_list):
        errors = {}
        for i, value in enumerate(value_list):
            try:
                for validator in self.validators:
                    value = validator(value)
            except ValidationError as ve:
                errors[i] = ve

            value_list[i] = value

        if errors:
            raise ValidationError(errors)
        return value_list
