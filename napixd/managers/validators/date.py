#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime

from napixd.exceptions import ValidationError


def ISO8601_date(iso_string):
    try:
        return datetime.datetime.strptime(iso_string, '%Y-%m-%d').date()
    except ValueError:
        raise ValidationError('Bad datetime format, Use ISO 8601 standard: yyyy-mm-dd')


def ISO8601_datetime(iso_string):
    try:
        return datetime.datetime.strptime(iso_string, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        raise ValidationError('Bad datetime format, Use ISO 8601 standard: yyyy-mm-ddThh:mm:ss')


class DatetimeBoundary(object):
    """
    Accepts the date in either the past or the future.
    """

    def __init__(self, direction=None, allow_past=True, allow_future=True):
        if direction is not None:
            if direction not in ('past', 'future'):
                raise ValueError('Direction must be past or future')
            allow_future = direction == 'future'
            allow_past = direction == 'past'
        elif not allow_past and not allow_future or allow_future and allow_past:
            raise ValueError('One of allow_future and allow_past must be set to True')
        else:
            direction = 'past' if allow_past else 'future'

        self.allow_future = allow_future
        self.allow_past = allow_past

        self.__doc__ = 'The date should be in the {0}'.format(direction)

    def __repr__(self):
        if self.allow_past:
            return '<Datetime in the past>'
        else:
            return '<Datetime in the future>'

    def __eq__(self, other):
        return (isinstance(other, DatetimeBoundary) and
                self.allow_past == other.allow_past and
                self.allow_future == other.allow_future)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __call__(self, date):
        now = datetime.datetime.now()
        if not self.allow_future and date > now:
            raise ValidationError('Date cannot be in the future')
        if not self.allow_past and date < now:
            raise ValidationError('Date cannot be in the past')
        return date
