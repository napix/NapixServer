#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.connectors.django import DjangoReadOperations, DjangoWriteOperations
from napixd.connectors.django import DjangoRelatedModelManager, DjangoModelManager
from napixd.managers import Manager
import tests.mock.django_models as models


class ROManager(DjangoReadOperations, Manager):
    model = models.Car
    resource_fields = {
        'name': {},
        'owner': {},
        'max_speed': {},
        'created': {'computed': True}
    }

    def get_queryset(self):
        return self.model.objects.all()


class WManager(DjangoWriteOperations, Manager):
    model = models.Car
    resource_fields = {
        'name': {},
        'owner': {},
        'max_speed': {},
        'created': {'computed': True}
    }

    def get_queryset(self):
        return self.model.objects.all()


class PM(DjangoModelManager):
    model_fields = ['name']
    model = models.Parent


class CM(DjangoRelatedModelManager):
    model_fields = ['name']
    model = models.Child
    related_to = models.Parent
