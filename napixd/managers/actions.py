#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Action are arbitrary python function that can be called
on a resource of a collection.
"""

import inspect
import warnings

from napixd.managers.resource_fields import (
    ResourceField,
    ResourceFields,
    ResourceFieldsDict,
    ResourceFieldsDescriptor,
)

__all__ = ('action', 'parameter')


def action(fn):
    """
    Decorates a python function that will be an action

    The action takes the :class:`resource<napixd.services.wrapper.ResourceWrapper>`
    as its first argument.

    The decorator automatically discovers the mandatory and optional arguments
    of the function and use them for documentation and template request generation.

    .. code-block:: python

        class RouterManager( Manager ):
            resource_fields = {
                    'ip' : {
                        'description' : 'IP of the target router'
                    }
                }
            ...
            @action
            def ping(self, router, tries=3):
                for x in xrange(tries):
                    if ping(router.resource['ip']):
                        return 'Router responds'
                return 'Router Unreachable'
    """
    return ActionProperty(fn)


def parameter(name, **kw):
    """
    Sets the meta-data on a parameter of an action.

    This decorator is applied on an action of a manager and set the meta-data
    on the argument *name* of the action. The meta-data are the same as the
    :attr:`napixd.managers.Manager.resource_fields` and are described in
    :class:`napixd.managers.resource_fields.ResourceField`.

    .. code-block:: python

        @action
        @parameter('tries',
            description='Number of times we try to ping'
            validators=[
                Mininum(1),
                Maximum(10),
                ])
        def ping(self, router, tries=3):
            for x in tries:
                if ping( router['ip']):
                    return 'Router responds'
            return 'Router Unreachable'

    Amongst other meta-data, a validator can reveive a list of
    :attr:`~napixd.managers.resource_fields.ResourceField.validators`, a
    :attr:`~napixd.managers.resource_fields.ResourceField.type` and
    :attr:`~napixd.managers.resource_fields.ResourceField.typing`,
    :attr:`~napixd.managers.resource_fields.ResourceField.choices`, etc,
    that are enforced before the method is called.

    There is no error when specifying
    :attr:`~napixd.managers.resource_fields.ResourceField.computed`,
    :attr:`~napixd.managers.resource_fields.ResourceField.editable`
    although it does not make sense.

    An action can reveive mutliple :func:`parameter` decorators for each of its
    arguments but each argument can only have a single :func:`parameter`
    decorator.
    """
    def inner_action_parameter(fn):
        if not hasattr(fn, 'resource_fields'):
            fn.resource_fields = {}

        if isinstance(fn.resource_fields, ResourceFields):
            warnings.warn('''You should use the decorator @action before
the decorator @parameter::

@action
@parameter(length, example=3, typing='static', type=int)
def cut_text(self, resource, length):
    return resource.text[:length]
''')
            rfs = list(fn.resource_fields)
            for i, rf in enumerate(rfs):
                if rf.name == name:
                    rfs[i] = ResourceField(name, rf, **kw)

                    fn.resource_fields = ResourceFields(rfs)
                    break
        else:
            rf = fn.resource_fields.setdefault(name, {})
            rf.update(kw)
        return fn
    return inner_action_parameter


class ActionProperty(object):

    def __init__(self, fn):
        self.function = fn
        self.__name__ = fn.__name__
        self.__doc__ = (fn.__doc__ or '').strip()

        self.mandatory, self.optional = self._extract(fn)

        resource_fields = getattr(fn, 'resource_fields', {})
        for param in self.mandatory:
            resource_fields.setdefault(param, {
                'example': '',
                'typing': 'dynamic',
            }).update({
                'optional': False,
            })

        for param, default in self.optional.items():
            rf = resource_fields.setdefault(param, {})
            rf.update({
                'optional': True
            })
            rf.setdefault('example', default)
            rf.setdefault('typing', 'dynamic' if default is None else 'static')

        self.resource_fields = ResourceFields(resource_fields)

    def __get__(self, instance, owner):
        if instance is None:
            return UnboundAction(self.function, self)
        return BoundAction(self.function, instance, self.resource_fields)

    def _extract(self, fn):
        param = inspect.getargspec(fn)
        # ignore first two parameters: self and resource
        args = param.args[2:]
        # default values
        opt = param.defaults or []

        # mandatory params = param list - param that have default values
        len_mand = len(args) - len(opt)
        mandatory = args[:len_mand]
        optional = dict(zip(args[len_mand:], opt))
        return mandatory, optional

    def __eq__(self, other):
        if isinstance(other, (UnboundAction, BoundAction, ActionProperty)):
            return other.function == self.function
        return False


class UnboundAction(object):

    def __init__(self, function, prop):
        self.function = function
        self.__name__ = prop.__name__
        self.__doc__ = prop.__doc__

        self.resource_fields = ResourceFieldsDict(
            function, prop.resource_fields)
        self.mandatory = prop.mandatory
        self.optional = prop.optional

    def __eq__(self, other):
        if isinstance(other, (UnboundAction, BoundAction, ActionProperty)):
            return other.function == self.function
        return False


class BoundAction(object):

    def __init__(self, function, manager, resource_fields):
        self.function = function
        self.manager = manager
        self.resource_fields = ResourceFieldsDescriptor(
            function, resource_fields)

    def __call__(self, resource, *args, **kwargs):
        return self.function(self.manager, resource, *args, **kwargs)

    def __eq__(self, other):
        if isinstance(other, (UnboundAction, BoundAction, ActionProperty)):
            return other.function == self.function
        return False
