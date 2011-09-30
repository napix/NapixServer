#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import Collection

class SimpleResource(Collection):
    """
    Adapteur qui permert à une classe qui represente une ressource
    d'implementer l'interface des collections
    """
    def __init__(self,klass):
        """
        crée un nouvel adapteur
        :param klass est la classe qui represente la resource
        """
        self.klass = klass
        for x in ('list','create','modify','delete'):
            #ajoute les propriétés implementées par la classe adaptée
            #dans cet adapteur
            if hasattr(klass,x):
                setattr(self,x,getattr(self,'_'+x))
        if not hasattr(klass,'get'):
            self.get = self._get
        self.fields = self.klass.fields

    def check_id(self,id_):
        """proxy de la classe adaptée"""
        return self.klass.check_id(id_)

    def _get(self,id_):
        """
        proxy de la classe adaptée
        par default renvoie un dictionnaire des champs declarés
        """
        child=self.klass.child(id_)
        res = {}
        for x in self.fields:
            res[x] = getattr(child,x)
        return res

    def _list(self,filters=None):
        """proxy de la classe adaptée"""
        return self.klass.list(filers = None)

    def _create(self,data):
        """proxy de la classe adaptée"""
        return self.klass.create(data)

    def _modify(self,id_,data):
        """proxy de la classe adaptée"""
        return self.klass.child(id_).modify(data)

    def _delete(self,id_):
        """proxy de la classe adaptée"""
        return self.klass.child(id_).delete()

