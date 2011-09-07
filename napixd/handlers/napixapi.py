#!/usr/bin/env python
# -*- coding: utf-8 -*-

from centrald.models import Client
from napixd.handler import Collection,Resource,Value

class APIUserHandler(Collection):
    """Gestionnaire des utilisateurs de l'API"""

    secret = Value('Mot de passe')

    @classmethod
    def find(cls,uid):
        try:
            return cls(Client.objects.get(uid))
        except Client.DoesNotExist:
            return None

    @classmethod
    def find_all(cls):
        return Client.objects.values_list('pk',flat=True)

    @classmethod
    def create(self,values):
        return Client.objects.create(**values)

    def remove(self):
        self.client.delete()

    def modify(self,values):
        self.value = values.pop('secret')
        self.save()

    def __str__(self):
        return self.client.pk

    def __init__(self,client):
        self.client = client

    def serialize(self):
        return { 'rid':self.client.pk,'secret':self.client.value }

class NAPIXAPI(Handler):
    """Service d'introspection de API"""
    url = 'napix'

    doc = Value('documentation du handler')
    fields = Value('Champs disponibles dans les ressources')
    collection_methods = Value('Methodes applicable à la collection')
    resource_methods = Value('Methodes applicable à la ressource')
    actions =Value('Actions applicable à la ressource')

    @classmethod
    def find_all(cls):
        from napixd.application import registry
        return registry.keys()

    @classmethod
    def find(cls,rid):
        from napixd.application import registry
        try:
            handler = registry[rid]
        except KeyError:
            return None
        y={}
        y.update(handler.doc_resource)
        y.update(handler.doc_collection)
        y.update(handler.doc_action)
        return cls(rid,**y)

