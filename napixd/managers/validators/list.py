#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.exceptions import ValidationError, ImproperlyConfigured


def not_empty(values):
    '''The list must not be empty'''
    if len(values) == 0:
        raise ValidationError('This list cannot be empty')
    return values


class Map(object):
    """
    Each value of the proposed list is submitted in order to each of the validators
    and the list of the results is returned.
    """
    def __init__(self, *validators):
        if not validators:
            raise ImproperlyConfigured('Map requires at least one validator')
        if not all(callable(v) for v in validators):
            raise ImproperlyConfigured('Map requires a list of validtors')

        self.validators = list(validators)
        self.__doc__ = '\n\n'.join(v.__doc__ or v.__name__ for v in self.validators)

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
