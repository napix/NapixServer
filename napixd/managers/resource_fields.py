#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ResourceFields is the property class of managers' resource_field.

It makes the documentation and the poperty homogenous.
"""

import collections
from napixd.exceptions import ImproperlyConfigured, ValidationError

__all__ = [
    'ResourceFields',
    'ResourceField',
    'ResourceFieldsDict',
    'ResourceFieldsDescriptor',
]


class ResourceFields(object):
    """
    The property object.

    When accessing it as a class property,
    it returns a dict-like object of the resource_fields.

    When it is accessed through a manager instance,
    it returns a :class:`ResourceFieldsDescriptor`.
    """
    def __init__(self, resource_fields, *overrides):
        self.values = []
        for rf in resource_fields:
            if not isinstance(rf, ResourceField):
                try:
                    rf = ResourceField(rf, resource_fields[rf])
                except ImproperlyConfigured as e:
                    raise ImproperlyConfigured('`{0}`: {1}'.format(rf, e))
            self.values.append(rf)

    def __iter__(self):
        return iter(self.values)

    def __get__(self, instance, owner):
        if instance is None:
            return ResourceFieldsDict(owner, self)
        return ResourceFieldsDescriptor(instance, self)


class ResourceFieldsDict(collections.Mapping):
    """
    The class view of the resource_fields

    It behaves as a dict.

    The fields returned are a combination of the properties of the
    :class:`ResourceField` and the :attr:`ResourceField.extra`
    and the extra **validate** member extracted from the corresponding
    :meth:`~napixd.managers.base.Manager.validate_resource_FIELDNAME`
    if it exists.
    """
    def __init__(self, manager_class, values):
        self.resource_fields = values
        self.values = {}
        for resource_field in values:
            field = resource_field.name
            field_meta = resource_field.resource_field()
            validation_method = getattr(manager_class,
                                        'validate_resource_' + field, None)

            if (hasattr(validation_method, '__doc__') and
                    validation_method.__doc__ is not None):
                field_meta['validation'] = validation_method.__doc__.strip()
            else:
                field_meta['validation'] = ''

            self.values[field] = field_meta

    def __getitem__(self, item):
        return self.values[item]

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return iter(self.values)

    def get_example_resource(self):
        """
        Returns the example resource found with the
        :attr:`~ResourceField.example` field of the resource fields.

        The :attr:`~ResourceField.computed` field are ignored.
        """
        example = {}
        for field in self.resource_fields:
            if field.computed:
                continue
            example[field.name] = field.example
        return example


class ResourceFieldsDescriptor(collections.Sequence):
    """
    The instance view of resource_fields

    This object manages the relations between a manager and its
    resource_fields.
    """
    def __init__(self, manager, values):
        self.manager = manager
        self.values = list(values)

    def __getitem__(self, item):
        return self.values[item]

    def __len__(self):
        return len(self.values)

    def serialize(self, raw):
        """
        Prepare the data from **raw** to be serialized to JSON.
        """
        dest = {}
        for k in self.values:
            try:
                dest[k.name] = raw[k.name]
            except KeyError:
                pass
        return dest

    def unserialize(self, raw):
        """
        Extract the data from **raw**.
        """
        dest = {}
        for k in self:
            try:
                dest[k.name] = raw[k.name]
            except KeyError:
                pass
        return dest

    def validate(self, input, original=None):
        """
        Validate the **input**.
        *original* is the actual value.

        Field are ignored and remove from *input* if

        * The property :attr:`ResourceField.computed` is set.
        * The property :attr:`ResourceField.editable` is not set
        and **original** is not None.

        A :exc:`napixd.exceptions.ValidationError` is raised when

        * A field is missing and is :attr:`ResourceField.required`.
        * A field does not satisfies :meth:`ResourceField.validate`.

        """
        for_edit = original is not None
        output = {}
        for resource_field in self:
            key = resource_field.name
            if (resource_field.computed or
                    for_edit and not resource_field.editable):
                if for_edit:
                    output[key] = original.get(key)
                continue
            elif key not in input:
                if resource_field.default_on_null:
                    value = None
                elif not resource_field.required:
                    continue
                else:
                    raise ValidationError({
                        key: u'Required'
                        })
            else:
                value = input[key]

            output[key] = resource_field.validate(self.manager, value)
        return output


class ResourceField(object):
    """
    The object for each resource_fields member.

    It takes as arguments the name on the field and the :class:`dict`
    of values defined in the creation
    of the :class:`napixd.managers.base.Manager` class.

    Some members have conditions, if those conditions are not met,
    :exc:`napixd.exceptions.ImproperlyConfigured` is raised.

    .. attribute:: example

        **Mandatory** unless :attr:`computed` or :attr:`choices` are used.

        If :attr:`type` is not defined, it is guessed from the example.
        If :attr:`type` is defined, :type:`example` must be an instance of it.

    .. attribute:: editable

        Set to False if the field is not writeable once the object is created.
        The field will be stripped from *resource_dict*
        before :meth:`napixd.managers.base.Manager.modify_resource` is called.

        :attr:`editable` is False if :attr:`computed` is True.

        Defaults to True

    .. attribute:: optional

        Set to True if the field is not required at all times.

        Defaults to False

    .. attribute:: default_on_null

        Set to True if the validation method can take ``None``
        as an input an generate a default value,
        when the field is not present.

        Defaults to False

    .. attribute:: typing

        One of **static** or **dynamic**.
        When typing is static,
        the validation checks the :attr:`type` of the input
        and raises a :exc:`~napixd.exceptions.ValidationError`
        if it does not match.

        When it is dynamic, the type is not enforced.

        Defaults to *static*

    .. attribute:: type

        The type of the field.

        Defaults to ``type(example)``

    .. attribute:: choices

        The valid values accepted for this field.

        Two kind of arguments are accepted:

        * A list, a set or an object with a __contains__ and a __iter__ method.
        * A callable returning such an object

        List is called with the object for the documentation of the manager.
        ``in`` is called to check
        is the value given by the user is a valid choice.

    .. attribute:: validators

        A list of additional validators.
        Validators are callback that takes a value and returns the validated value,
        or raises a :exc:`napixd.exceptions.ValidationError`.

        .. code-block:: python

            def size_is_4(value):
                if len(value) != 4:
                    raise ValidationError('Size should be 4')
                #Always return the value
                return value

            def looks_like_an_int(value):
                if not value.isdigit():
                    raise ValidationError('Value should be an int')
                return value

            class SecurityCards(Manager):
                resource_fields = {
                    'pin' : {
                        'example': '1234',
                        'validators': [ size_is_4, looks_like_an_int ]
                    }
                }


    .. attribute:: extra

        All the fields from the resource_field which are not a property.
        Those fields are not used by the Napix Server
        but may be useful to the clients.

        :description:
            The goal of the field.

        :display_order:
            The priority of the field.
            The fields with a lower *display_order* are shown first.

    """
    def __init__(self, name, values, **overrides):
        if isinstance(values, ResourceField):
            rf = values
            values = {
                'editable': values.editable,
                'optional': values.optional,
                'computed': values.computed,
                'default_on_null': values.default_on_null,
                'typing': values.typing,
                'validators': values.validators,
            }
            values.update(rf.extra)
        elif not isinstance(values, collections.Mapping):
            raise ImproperlyConfigured(
                'Resource field declaration is not a dict')
        self.name = name

        if overrides:
            values.update(overrides)

        meta = {
            'editable': True,
            'optional': False,
            'computed': False,
            'default_on_null': False,
            'typing': 'static',
            'validators': []
            }
        extra_keys = set(values).difference(meta)
        meta.update(values)

        self.optional = meta['optional']
        self.computed = meta['computed']
        self.default_on_null = meta['default_on_null']

        self.editable = not self.computed and meta.get('editable', True)

        explicit_type = meta.get('type')
        if explicit_type and not isinstance(explicit_type, type):
            raise ImproperlyConfigured('type field must be a class')

        try:
            choices = meta['choices']
        except KeyError:
            choices = None
        else:
            if not callable(choices) and not hasattr(choices, '__iter__'):
                raise ImproperlyConfigured('choices must be a callable or an iterable')
        self.choices = choices

        if choices and not explicit_type:
            types = set(type(choice) for choice in self.get_choices())
            if len(types) != 1:
                raise ImproperlyConfigured('The choices should all have the same type')
            explicit_type = types.pop()

        try:
            self.example = meta['example']
        except KeyError:
            if self.computed:
                self.example = u''
            elif choices:
                choices_list = self.get_choices()
                try:
                    self.example = choices_list[0]
                except IndexError:
                    raise ImproperlyConfigured('There should be at least one choice')
            else:
                raise ImproperlyConfigured('Missing example')

        implicit_type = type(self.example)
        if implicit_type is str:
            implicit_type = unicode

        self.type = explicit_type or implicit_type
        self.typing = meta['typing']

        if self.typing == 'dynamic':
            if self.choices is not None:
                raise ImproperlyConfigured('Choices are not usable with dynamic typing')
            self._dynamic_typing = True
        elif self.typing == 'static':
            self._dynamic_typing = False
            if type(self.example) != self.type and not self.computed:
                if self.type is unicode and isinstance(self.example, str):
                    self.example = unicode(self.example)
                elif not self.check_type(self.example):
                    raise ImproperlyConfigured(
                        'Example is not of type {0}'.format(self.type.__name__))
        else:
            raise ImproperlyConfigured('Typing must be one of "static", "dynamic"')

        self.validators = list(meta['validators'])

        self.extra = dict((k, values[k]) for k in extra_keys)

    def __repr__(self):
        return 'Field <{0}>'.format(self.name)

    def check_type(self, value):
        """
        Check the :attr:`type` of **value**.

        It is always returns True if :attr:`typing` is **dynamic**.
        """
        if value is None and self.default_on_null:
            return True
        elif self._dynamic_typing:
            return True
        elif self.type == int and isinstance(value, long):
            return True
        elif self.type == str and isinstance(value, unicode):
            return True
        elif self.type == float and isinstance(value, (long, int)):
            return True
        else:
            return isinstance(value, self.type)

    @property
    def required(self):
        """
        The field is :attr:`optional` or :attr:`computed`
        """
        return not (self.optional or self.computed)

    def resource_field(self):
        values = dict(self.extra)
        values.update({
            'editable': self.editable,
            'optional': self.optional,
            'computed': self.computed,
            'default_on_null': self.default_on_null,
            'example': self.example,
            'typing': 'dynamic' if self._dynamic_typing else 'static',
            'choices': (list(self.get_choices())
                        if self.choices is not None else None),
            'validators': [validator.__doc__ for validator in self.validators]
            })

        if self.type in (str, basestring, unicode):
            values['type'] = 'string'
        else:
            values['type'] = self.type.__name__

        return values

    def validate(self, manager, value):
        """
        Validate the input **value**.
        """
        if not self.check_type(value):
            raise ValidationError({
                self.name: u'Bad type: {0} has type {2} but should be {1}'.format(
                    self.name, self.type.__name__, type(value).__name__)
            })
        if self.choices is not None:
            self.check_choice(value)

        validator = getattr(manager, 'validate_resource_%s' % self.name, None)
        if validator:
            value = self._run_callback(validator, value)
        for validator in self.validators:
            value = self._run_callback(validator, value)

        return value

    def _run_callback(self, callback, value):
        try:
            return callback(value)
        except ValidationError, e:
            raise ValidationError({
                self.name: unicode(e)
            })

    def get_choices(self):
        """
        Returns the choices of this field.

        If :attr:`choices` is a callable, it is called.
        """
        if callable(self.choices):
            return self.choices()
        return self.choices

    def check_choice(self, value):
        """
        Check that the value(s) fits the choices.

        If value is an iterable (except strings),
        it checks that **value** is a subset of :attr:`choices`
        else it checks that **value** is in :attr:`choices`.
        """
        choices = self.get_choices()
        if isinstance(value, basestring) or not hasattr(value, '__iter__'):
            value = [value]

        for v in value:
            if not v in choices:
                raise ValidationError({
                    self.name: u'{0} is not one of the available choices'.format(v)
                    })
