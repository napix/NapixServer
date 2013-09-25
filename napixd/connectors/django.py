#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
====================
Connector for django
====================
"""

from __future__ import absolute_import

import os
import logging

import django
import django.conf
settings = django.conf.settings

from napixd.conf import Conf
from napixd.managers import Manager
from napixd.managers.mixins import AttrResourceMixin
from napixd.exceptions import ValidationError, NotFound

logger = logging.getLogger('Napix.connectors.django')


class DjangoImport(object):

    """
    Context Manager used to initialize django before importing a model.

    If ``module`` is not specified,
    it defaults to the configuration key `Napix.connectors.django`.

    If ``module`` ( or the configuration key) is a string, it will be used
    as the module name to the settings module of the django application
    (cf ``DJANGO_SETTINGS_MODULE``).
    Else it must be a mapping which keys are used to configure django
    (cf :meth:`django.conf.settings.configure`).

    .. code-block:: python

        from napixd.connectors.django import DjangoImport

        with DjangoImport( 'myproject.settings''):
            from myapp.models import MyModel
    """

    _module = None

    def __init__(self, module=None):
        self.module = module or Conf.get_default('Napix.connectors.django')

    def __enter__(self):
        if not settings.configured:
            self.__class__._module = self.module

            if isinstance(self.module, basestring):
                os.environ['DJANGO_SETTINGS_MODULE'] = self.module
                logger.info(
                    'Import django with settings module %s', self.module)
            else:
                settings.configure(**self.module)
                logger.info('Import django with settings dict')

        elif self.module == self.__class__._module:
            logger.debug('Django is already configured')
        else:
            raise RuntimeError('Different django settings are already used')

    def __exit__(self, exc_type, exc_value, tb):
        pass


class DjangoModelManagerMeta(type(Manager)):

    def __new__(self, name, bases, attrs):
        model = attrs.get('model')
        if model:
            resource_fields = self._get_resource_fields_from_model(model)
            if 'resource_fields' in attrs:
                rf = set(attrs['resource_fields'])
                for field in rf.intersection(resource_fields.iterkeys()):
                    resource_fields[field].update(
                        attrs['resource_fields'][field])
                for field in rf.difference(resource_fields.iterkeys()):
                    resource_fields[field] = attrs['resource_fields'][field]

            if 'model_fields' in attrs:
                resource_fields = dict((key, resource_fields[key])
                                       for key in attrs['model_fields'])
            if 'model_fields_exclude' in attrs:
                exclude_fields = set(attrs['model_fields_exclude'])
                resource_fields = dict((key, resource_fields[key])
                                       for key in resource_fields
                                       if key not in exclude_fields)

            attrs['resource_fields'] = resource_fields

            if not attrs.get('queryset'):
                attrs['queryset'] = model.objects

        return super(DjangoModelManagerMeta, self).__new__(
            self, name, bases, attrs)

    @classmethod
    def _get_resource_fields_from_model(self, model):
        resource_fields = {}
        for field, a in model._meta.get_fields_with_model():
            resource_fields[field.name] = {
                'description': field.help_text,
                'optional': field.null or field.blank,
                'computed': (
                    getattr(field, 'auto_now', False) or
                    getattr(field, 'auto_now_add', False) or
                    field.auto_created)
            }
        return resource_fields


class BaseDjangoModelManager(Manager):
    __metaclass__ = DjangoModelManagerMeta

    queryset = None
    model = None

    def get_queryset(self):
        return self.queryset.all()

    @classmethod
    def get_name(cls):
        """
        Returns the lower case model name.
        """
        return (cls.name or cls.model and cls.model._meta.name.lower() or
                super(BaseDjangoModelManager, cls).get_name())


class DjangoReadOperations(AttrResourceMixin, object):

    def get_resource(self, id_):
        """
        Get a resource by its pk.
        """
        try:
            return self.get_queryset().get(pk=id_)
        except self.model.DoesNotExist:
            raise NotFound(id_)

    def list_resource(self):
        """
        List the pk of the resource.
        """
        return self.get_queryset().values_list('pk', flat=True)


class DjangoWriteOperations(object):

    def validate_resource(self, resource_dict):
        try:
            for field_name in resource_dict:
                field, b, c, d = self.model._meta.get_field_by_name(field_name)
                proposed = resource_dict[field_name]
                for validator in field.validators:
                    validator(proposed)
        except django.core.exceptions.ValidationError, e:
            raise ValidationError('%s is not valid: %s' % (field_name, e))
        else:
            return resource_dict

    def create_resource(self, resource_dict):
        model = self.get_queryset().create(**resource_dict)
        return model.pk

    def _get_model(self, id_):
        try:
            return self.get_queryset().get(pk=id_)
        except self.model.DoesNotExist:
            raise NotFound(id_)

    def delete_resource(self, id_):
        self._get_model(id_).delete()

    def modify_resource(self, id_, resource_dict):
        model = self._get_model(id_)
        for k, v in resource_dict.items():
            setattr(model, k, v)
        model.save()


class DjangoReadOnlyModelManager(DjangoReadOperations, BaseDjangoModelManager):

    """
    Subclass of :class:`napixd.managers.base.Manager`
    which is specified for a django model.

    .. attribute:: model

        The :class:`django.db.models.Model` used for this manager.

    .. attribute:: model_fields

        Iterables of the included model fields.

        If specified,
        only the fields of the model given in this set will be used.

    .. attribute:: model_fields_exclude

        Like :attr:`model_fields`, but explicitely exclude the fields.
        When both are specified, model_fields_exclude has the precedence.

    .. attribute:: resource_fields

        Resource fields of this manager.
        See :attr:`managers.Manager.resource_fields`.

        This attribute is computed from the meta of the model.

        If the class defines its own resource_fields, it is merged with the
        resource_fields generated.
        The additional fields are added,
        the content of existing fields is merged.

        To remove fields from resource_fields, use :attr:`model_fields_exclude`.

        .. code-block:: python

            class Account( models.Model ):
                number = models.CharField(
                    max_lentgh=200, help_text='Person owning this account')
                owner = models.CharField(max_lentgh=1000)
                creation_date = models.DateField( auto_now_add=True)

            class BankAccountManager(DjangoReadOnlyModelManager ):
                model = Account
                resource_fields = {
                    'owner' : {
                        'description':
                        'Customer of the bank to wich the account is attached.'
                    },
                    'balance': {
                        'description': 'Amount of money in this account'
                        'computed': True
                    }
                }

            BankAccountManager.resource_fields
            {
                'number': {
                    'description': 'Customer of the bank to wich the account is attached.'
                },
                'owner' : {
                    'description': 'Person owning this account',
                },
                'balance' : {
                    'description': 'Amount of money in this account'
                    'computed': True
                }
                'creation_date': {
                    'description':  '',
                    'computed': True
                }
            }


    .. attribute:: queryset

        A django queryset or manager.

        When this property is not defined, it's the default manager of :attr:`model` .
    """
    pass


class DjangoModelManager(
        DjangoWriteOperations, DjangoReadOperations, BaseDjangoModelManager):
    """
    Sub class of :class:`DjangoReadOnlyModelManager`
    which adds the modification/deletion/creation operations.
    """
    pass


class DjangoRelatedModelManagerMeta(DjangoModelManagerMeta):

    def __new__(self, name, bases, attrs):
        if 'related_to' in attrs:
            model = attrs['model']
            if not 'related_by' in attrs:
                related_to = attrs['related_to']
                relations = [x.related.get_accessor_name()
                             for x, y in model._meta.get_fields_with_model()
                             if x.rel and (
                                 x.rel.to is related_to or
                                 x.rel.to.__name__ == related_to)]
                attrs['related_by'] = relations[0]

        return super(DjangoRelatedModelManagerMeta, self).__new__(
            self, name, bases, attrs)


class BaseDjangoRelatedManager(BaseDjangoModelManager):
    __metaclass__ = DjangoRelatedModelManagerMeta

    @classmethod
    def detect(cls):
        """
        Override :meth:`~napixd.managers.Manager.detect` to always return false.
        This manager is supposed to be used inside a managed_class
        and get a model as its parent.
        """
        return False

    def get_queryset(self):
        """
        Returns a copy of :attr:`queryset`.

        Can be overridden to return a custom queryset
        """
        return getattr(self.parent, self.related_by)


class DjangoRelatedModelManager(
        DjangoWriteOperations, DjangoReadOperations, BaseDjangoRelatedManager):
    """
    Sub class of :class:`DjangoModelManager`
    which is suitable for a related object.

    Those manager are intended to be used as managed_class
    of a Manager of the related model.

    .. attribute:: related_to

        The model or the name of the model to which this manager is related.

        .. code-block:: python

            class PollManager(DjangoModelManager):
                model = Poll

            class AnswerManager(DjangoRelatedModelManager):
                model = Answer
                related_to = Poll

    .. attribute:: related_by

        The name of the relation.

        It is required if there is more than one relation between the two models.
    """
    pass
