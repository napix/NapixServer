#!/usr/bin/python
# -*- coding: iso-8859-15 -*- 


import os, glob, sys




"""
Besoin exemple :
Gestion d'user : lister le contenu d'un fichier, chaque ressource est une ligne
Gestion d'userbis : executer une commande pour lister (voir lire le contenu d'un fichier), invoquer les commandes adéquates pour effacer
Gestion de DNS : liste de zone, les zones ont des propriété (SOA, etc) et chaque enregistrement est ensuite une ressource avec ses propriétés
Gestion de configuration apache : lister les vhost (parsing de fichier), les vhost sont des bout de fichier
Gestion de configuration apache bis : lister les fichier dans le /etc/apache2/host-enabled, les vhost sont des fichiers
Gestion des script init.d : liste les fichier dispo, exporte une action par service
Gestion de vm : liste les vms, chaque vm dispose de ces propres actions (execution de script, etc) et la recup de toute la ressource demande plusieurs execution.
                Le Manager des vms dispose lui meme d'action ...?
Gestion du reseau : exporte la collection des vlans, des switchs, etc ; on doit pouvoir ajouter un vlan a un switch mais aussi un switch a un vlan simplement
Gestion des users openvpn : liste des users dans un fichier, execution d'une commande lors de la création/deletion/modification pour reprogrammer les regles iptables

"""


class CheckField(type):
    def __new__(meta, classname, bases, classDict):
        if "fields" not in classDict:
            raise ValueError("Your ressource class *must* have fields defined")
        for name, desc in classDict["fields"]:
            if "eg:" not in desc:
                print "Warning : no exemple in the definition of field %s"%name
        return type.__new__(meta, classname, bases, classDict)
            

class Ressource(dict):
    """ BaseType for ressource. Just a dict """
    __metaclass__ = CheckField
    
    fields = {}
    
    def __init__(self, *l, **kv):
        dict.__init__(self, *l, **kv)
        missingfields = [ field for field in self.fields if field not in self ]
        if missingfields:
            raise KeyError("Sorry, the following field are missing : %s"%", ".join(missingfields))


class MyBignou:
    #################################
    # La partie manager
    #################################
    ressources = {} # { "id" : dict() } afin de representer les values
    def configure(self, conf):
        # Configure les parametres de l'objet.
        pass
    def load(self):
        # Faire ce qu'il faut s'il a besoin de loader des trucs.
        pass
    def get(self, id):
        # retourne un dict de l'objet en question
        pass
    def create(self, params):
        # cree un nouveau objet
        # si pas de id dans params alors on en alloc un tout seul si on peut
        pass
    def delete(self, id):
        # efface l'objet
        obj = self.get(id)
        if hasattr(obj, "handler_delete"):
            obj.handler_delete()
        del self.ressources[id]
        self.commit()
    def modify(self, id, param):
        # on modifie.
        self.create(param)
        self.delete(id)
    def list(self):
        # on recupere la liste des id des sous objets
        pass
    def commit(self):
        # On passe les changement au systeme
        pass

    def validate(self, jsondict):
        # on valide les datas pour s'assurer qu'elles sont cachere pour l'input
        pass

    #################################
    # La partie ressource
    #################################
    fields = { "name": "description, eg: valeurexemple",
               "name2": "description, eg: valeurexemple" }
    #On parse automatiquement le contenu de field, on override l'init afin de forcer la présence des champs a
    #la création de l'objet. De plus, on découpe sur eg: afin de recuperer les valeurs par defaut
    #il est a noter que la ressource doit savoir travailler avec des strings.
    def handler_delete(self):
        # handler appelé quand on delete. Par defaut, on liste nos eventuels fils et on leur delete la gueule
        for i in self.list():
            self.delete(i)
    def handler_create(self):
        # handler appelé a la création d'un nouvel objet par l'utilisateur
        pass
    def action_machinchose(self, param):
        # permet d'executer une action arbitraire.
        # si jamais cette action doit se faire juste sur un id, alors param sera egal a l'id de la ressource
        # a modifier, c'est ce qui fait qu'on dit que c'est une methode de ressource
        
        

"""
Plusieur type de manager par defaut :
 - Manager conteneur uniquement, n'a pas de logique, appele juste les handler sur les objets ressources qu'il cree et qui savent se demerder tout seul
 - Manager qui manage des ressources sans inteligence, a besoin d'une definition de ressource minimal pour travailler et sais repercuter tout les changements
 - Manager + ressource fait pour manager des snippets de fichier de conf ? Besoin juste d'un parser (==regex ?) et d'un dumper
 - Manager fait pour contenir des managers : permet juste de ranger les choses facilement sous nos objets

"""

    

class CollectionManager(object):
    """Class used to manage a collection of ressource.
    """
    
    def __init__(self, subressourcetype = Ressource, discriminant = None):
        self.subressourcetype = subressourcetype
        self.discriminant = None # Not sure if we'll want to use it.
        self.subressources = []

    def sub_list(self, *l, **kv):
        """ Return a list of id of managed ressource """
        # Try to get this list from the find_all classmethod of the managed ressource
        find_all = getattr(self.subressourcetype, "find_all", None)
        if find_all:
            if not find_all.im_self:
                raise TypeError("Your find_all method must be a classmethod")
            return find_all(*l, **kv)
        raise NotImplementedError("You must provide your own way to discover your ressource"
                                  "either by overriding the listchildren method of your collectionmanager class"
                                  "or by writing a @classmethod named find_all on your ressource class")

    def sub_get(self, id):
        """ Return an instanciated ressource from the specified id """
        find_instance = getattr(self.subressourcetype, "find_instance", None)
        if find_instance:
            if not find_instance.im_self:
                raise TypeError("Your find_instance method must be a classmethod")
            return find_instance(id)
        raise NotImplementedError("You must provide your own way to create a ressource object"
                                  "either by overriding the getchild method of your collectionmanager class"
                                  "or by writing a @classmethod named find on your ressource class")

    def sub_create(self, params):
        return self.subressourcetype(**params)

    def sub_modify(self, subressource, params):
        new = self.sub_create(self, params)
        if not new:
            raise ValueError("FIXME : Something obviously get wrong")
        # FIXME : find a way to not call handle_create and handle_delete.
        #if hasattr(new, "handle_modify"):
        #    new.handle_modify(subressource)
        self.sub_delete(subressource)
        self.sub_save()

    def sub_save(self):
        """ Commit the current collection status to the disk. This method is called everytime a subressource is modified"""
        pass

    def do_list(self, force_refresh=False):
        """ Return a list of subressource """
        if force_refresh:
            self.subressources = []
        if not self.subressources:
            self.subressources = self.listressource()
        return self.subressources[:] # May be we won't have to force a copy ?

    def do_create(self, params):
        """ Create a subressource using params """
        pass
        

class CollectionOfCollectionManager(CollectionManager):
    """This method is used to represent a collection of collection. Use it
    when some of your ressource have multiple type of subressource so you
    can't just nest them directly.
    """
    
    def __init__(self, collections):
        """ You can specify collections as a dict
        eg : { 'Record': RecordCollectionManager() }
        FIXME : better DOC :D
        """
        CollectionManager.__init__(self, subressourcetype=None)
        self.collections = collections

    def sub_list(self):
        return [ i for i in self.collections ]

    def sub_get(self, id):
        return self.collections[id]

    sub_create = None
    sub_delete = None
