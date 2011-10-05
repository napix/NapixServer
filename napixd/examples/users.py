#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.resources.by_resource import SimpleResource
from napixd.exceptions import ValidationError,NotFound
from napixd.executor import executor
import pwd


"""
Example de module de gestion d'utilisateurs ecrit par la resource
"""

#Un gestionnaire de ressource ecrit par la ressource est une classe
# qui represente la ressource.
# Les methodes de collection definies par l'interface service et 
# check_id sont implementées avec des classmethod
# child retourne une instance de la classe elle meme
# Les methodes des ressource sont implementés par des methodes d'instance
# sauf qu'elle ne prennent pas le paramatres ID
# par defaut le get recupère les attribut de l'instance qui sont définis dans fields

class User(object):
    #definition des champs de la classe
    # Sert lors des requetes GET,par default l'implementation de
    # SimpleCollection.get retourne un dictionaire ne contenant que les champs
    # déclarés dans fields.
    # Filtre aussi les données envoyés dans la requete lors des POST et des PUT
    fields = ['uid','username','shell']

    #Verification de l'identifiant
    # tout les identifiants passés aux methodes appelés par le Service sont passé par cette methode
    # retourne une version adaptée de l'identifiant: ici, la chaine est convertie en entier
    # Si l'identifiant n'est pas un identifiant valide, jete une exception ValidationError
    # Par default, il est verifié que l'id n'est pas une chaine vide
    @classmethod
    def check_id(cls,id_):
        try:
            return int(id_)
        except (ValueError,TypeError):
            raise ValidationError

    #methode de création d'un resource.
    # appelé lors d'un POST sur la collection
    # prends en parametre un dictionnaire de données filtrées
    # retourne le nouvel identifiant de la resource generée
    @classmethod
    def create(cls,data):
        command = ['/usr/sbin/useradd']
        if 'uid' in data:
            command.append('-u')
            command.append(data['uid'])
        if 'shell' in data:
            command.append('-s')
            command.append(data['shell'])
        command.append(data['username'])
        rc = executor.create_job(command).wait()
        if rc == 0:
            return pwd.getpwnam(data['username']).pw_uid

    #methode de listage des resources
    # appelé lors d'un GET sur la collection
    # prends en parametre un dictionnaire qui a été transmis par GET et qui represente
    # des filtres ou des pages
    @classmethod
    def list(cls,filters):
        return [x.pw_uid for x in pwd.getpwall()]

    #prends un id qui est l'identifiant de la resource au niveau de service
    #retourne une instance de la classe
    @classmethod
    def child(cls,id_):
        try:
            user = pwd.getpwuid(id_)
        except KeyError:
            raise NotFound
        return cls(user)

    #initialize la ressource, les propriété definies sont arbitraires
    def __init__(self,user):
        self.uid = user.pw_uid
        self.username = user.pw_name
        self.shell = user.pw_shell

    #methode de suppression de l'instance
    def delete(self):
        command = ['/usr/bin/userdel']
        command.append(self.username)
        rc = executor.create_job(command).wait()


class UserManager(SimpleResource):
    def __init__(self):
        super(UserManager,self).__init__(User)

