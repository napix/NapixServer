#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.resources.by_collection import SimpleCollection
from napixd.exceptions import ValidationError,NotFound
from napixd.executor import executor
import pwd

"""
Example de module de gestion d'utilisateurs ecrit par la collection
"""

#Un gestionnaire de ressource qui hérite de SimpleCollection doit definir
# le sous-ensemble de l'interface service qui correspond au besoin
# SAUF la methode child qui doit être ecrite sous le nom de get_child

#la classe SimpleCollection comporte une implementation de child
# qui appele la methode get_child de la classe fille et encapsule
# le resultat dans une classe de resources qui implemente l'interface du service

#SimpleCollection comprends aussi par default une implementation de get qui
#retourne le contenu du dictionnaire retourné par child() filtrés des clés qui ne sont
#pas dans fields

class User(SimpleCollection):
    """
    La classe User va gerer les utilisateurs système
    Une instance de cette classe sera utilisé par un objet Service qui appelera les methodes definies.
    """

    #definition des champs de la classe
    # Sert lors des requetes GET,par default l'implementation de
    # SimpleCollection.get retourne un dictionaire ne contenant que les champs
    # déclarés dans fields.
    # Filtre aussi les données envoyés dans la requete lors des POST et des PUT
    fields = ['uid','username','shell']

    #declaration optionnelle d'une resource_class qui serait une classe
    # implementant l'interface du service
    #SimpleCollection a une valeur par défaut
    ##resource_class = CustomClass

    #Verification de l'identifiant
    # tout les identifiants passés aux methodes appelés par le Service sont passé par cette methode
    # retourne une version adaptée de l'identifiant: ici, la chaine est convertie en entier
    # Si l'identifiant n'est pas un identifiant valide, jete une exception ValidationError
    # Par default, il est verifié que l'id n'est pas une chaine vide
    def check_id(self,id_):
        try:
            return int(id_)
        except (ValueError,TypeError):
            raise ValidationError

    #methode de création d'un resource.
    # appelé lors d'un POST sur la collection
    # prends en parametre un dictionnaire de données filtrées
    # retourne le nouvel identifiant de la resource generée
    def create(self,data):
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
    def list(self,filters):
        return [x.pw_uid for x in pwd.getpwall()]

    #methode appelée par SimpleCollection
    # prends un id qui est l'identifiant de la resource au niveau de service
    # retourne un dictionnaire de valeurs arbitraires qui sera encapsulé dand
    # la resource_class
    def get_child(self,id_):
        try:
            user = pwd.getpwuid(id_)
        except KeyError:
            raise NotFound
        return {'uid':user.pw_uid,'username':user.pw_name,'shell':user.pw_shell}

    #methode de suppression de l'instance
    #supprime l'element designé par username
    def delete(self,username):
        command = ['/usr/bin/userdel']
        command.append(username)
        rc = executor.create_job(command).wait()

