#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Validators package for date inputs.

Napix does not natively supports dates, but it promotes two ways of handling them.
First a :class:`int` resource field that contains a timestamp, and a string type
that contains a ISO 8601 date.
"""


import datetime

from napixd.exceptions import ValidationError


def ISO8601_date(iso_string):
    """
    Parses a date and returns a :class:`datetime.date` object.

    Invalid dates raise a :exc:`napixd.exceptions.ValidationError`.
    """
    try:
        return datetime.datetime.strptime(iso_string, '%Y-%m-%d').date()
    except ValueError:
        raise ValidationError('Bad datetime format, Use ISO 8601 standard: yyyy-mm-dd')


def ISO8601_datetime(iso_string):
    """
    Parses a datetime and returns a :class:`datetime.datetime` object.

    Invalid datetimes raise a :exc:`napixd.exceptions.ValidationError`.
    """
    try:
        return datetime.datetime.strptime(iso_string, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        raise ValidationError('Bad datetime format, Use ISO 8601 standard: yyyy-mm-ddThh:mm:ss')


class DatetimeBoundary(object):
    """
    Check that the datetime is either in the future or in the past.
    """
    def __init__(self, allow_past=True, allow_future=True):
        self.allow_future = allow_future
        self.allow_past = allow_past

    def __call__(self, date):
        now = datetime.datetime.now()
        if not self.allow_future and date > now:
            raise ValidationError('Date cannot be in the future')
        if not self.allow_past and date < now:
            raise ValidationError('Date cannot be in the past')
        return date
