#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.exceptions import NotFound
from . import Collection

class SimpleCollectionResource(dict,Collection):
    """
    dictionnaire implementant l'interface des ressource et des collections
    qui fait par default la laison entre les enfants des SimpleCollection
    et les sous collections
    """
    def child(self,subfile):
        """
        Recupere la sous collection :param subfile
        """
        try:
            #Les sous collections sont installées par la metaclass
            #dans cette classe
            return getattr(self,subfile)
        except AttributeError:
            raise NotFound,subfile

    def get(self):
        """retourne une copie de self debarassée des properties"""
        return dict(self)

    def list(self,filters=None):
        """Liste les sous-collections disponibles"""
        return self._subresources

class SubResource(object):
    """Installe une sous ressource dans une SimpleCollection"""
    def __init__(self,subclass):
        """:param subclass est la sous class de la ressource"""
        self.subclass = subclass
    def __get__(self,instance,owner):
        """retourne une instance de la sous collection pour la ressource donnée"""
        if instance is None:
            return self.subclass
        return self.subclass(instance)

class SimpleCollection(Collection):
    """
    Classe de base de la collection
    Les classes qui heritent de celle-ci doivent implementer les methodes de l'interface
     service correspondantes aux besoins.
    SAUF child qui ne doit pas être surchargée
    SAUF get qui peut être surchargé
    """

    #class par default
    resource_class = SimpleCollectionResource

    def get(self,ident):
        """filtre le dict de la ressource"""
        child = self.child(ident)
        return dict([(key,child[key])
            for key in child
            if key in self.fields])

    def get_child(self,id_):
        """Recupère le fils de la collection"""
        raise NotImplementedError

    def child(self,id_):
        """crée une instance de la resource_class pour la resource"""
        child = self.get_child(id_)
        return self.resource_class(child)

