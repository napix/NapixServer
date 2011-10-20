#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import functools

import bottle
from bottle import HTTPError
from napixd.exceptions import NotFound,ValidationError,Duplicate

"""
The service class ack like a proxy between bottle and napix resource Manager Component.

It handle bottle registering, url routing and Manager configuration when needed.


"""

class ArgumentsPlugin(object):
    """
    Plugin qui filtre les mots clés de la requête pour les passer par liste
    Workaround du fait que bottle ne passe les arguments que par mot clé

    FIXME : Quel est le cas ou cela doit servir ? Comprends pas !
    FIXME : Si par exemple
    """
    name='argument'
    api = 2
    def apply(self,callback,route):
        @functools.wraps(callback)
        def inner(*args,**kw):
            path = self._get_path(args,kw)
            return callback(bottle.request,path)
        return inner

    def _get_path(self,args,kw):
        #FIXME : ca fait quoi ce truc ???
        #FIXME : mettre un exemple.
        #FIXME : et puis d'abord les lambdas c'est moche
        # On remap le format interne fxxx vers un entier pour le tri (et eviter les probleme si xxx > 10)
        # a = [ (int(k.replace("f", "")), v) for k, v in kw ]
        # # On veut les arguments trié dans l'ordre
        # a.sort()
        # return [ v for k,v in a ]
        # ou
        # result = []
        # for i in range(len(kw)):
        #     try: result.append(kw["f%i"%i])
        #     except: return result
        # (c'est vraiment pourri comme truc pour stocker les arguments quand meme ...)
        if args :
            return args
        return map(lambda x:kw[x],
                itertools.takewhile(lambda x:x in kw,
                    itertools.imap(lambda x:'f%i'%x,
                        itertools.count())))

class Service(object):
    """Class qui sert d'interface entre une application bottle et les collections
    FIXME : c'est la classe qui est déstinée a être overrider, le préciser."""
    def __init__(self,collection):
        """crée un nouveau service pour la collection donnée"""
        self.collection = collection()
        # FIXME : ca c'est bien par defaut, mais il faut qu'on puisse le préciser dans le fichier de conf
        self.url = collection.__name__.lower()

    def setup_bottle(self,app):
        """Enregistre le service sur l'application bottle passée"""
        self._setup_bottle(app,self.collection,'/'+self.url,0)

    def _setup_bottle(self,app,collection,prefix,level):
        """Fonction récursive pour enregister une collection et ses sous-collections"""
        app.route('%s'%(prefix),method='ANY',callback=self.as_resource,apply=ArgumentsPlugin)
        next_prefix = '%s/:f%i'%(prefix,level)
        app.route('%s/'%(prefix),method='ANY',callback=self.as_collection,apply=ArgumentsPlugin)
        if hasattr(collection,'resource_class'):
            self._setup_bottle(app,collection.resource_class,next_prefix,level+1)
            if hasattr(collection.resource_class,'_subresources'):
                for sr in collection.resource_class._subresources:
                    self._setup_bottle(app,getattr(collection.resource_class,sr),
                            '%s/:f%i'%(next_prefix,level+1),level+2)

    def as_resource(self,request,path):
        """Callback appellé pour une requete demandant une collection"""
        return ServiceResourceRequest(request,path,
                self.collection).handle()

    def as_collection(self,request,path):
        """Callback appellé pour une requete demandant une resource"""
        return ServiceCollectionRequest(request,path,
                self.collection).handle()

class ServiceRequest(object):
    """Objet créé pour servir une requete
    FIXME : cette classe appele ensuite les methode de la classe service ? Si oui
    le préciser, dire dans quel contexte."""
    def __init__(self,request,path,collection):
        """
        Crée l'objet qui sert la requete request sur collection
        en demandant l'objet designé par path
        FIXME : en demandant l'objet ? la ressource plutot ?
        """
        self.request = request
        self.method = request.method
        self.base_collection = collection
        self.path = path

    def check_datas(self,collection):
        """Verifie que les champs passés sont dans les champs de la collection
        FIXME : Un validator s'appele validate_xxx :)
        Préciser que la fonction retourne un dictionnaire épurée de tout clé
        n'étant pas présent dans la propriété field de la collection
        """
        data = {}
        for x in self.request.data:
            if x in collection.fields:
                data[x] = self.request.data[x]
        return data

    def get_collection(self):
        """
        Récupere la collection correspondante à la requete
        """
        node = self.base_collection
        for child in self.path:
            #verifie l'id de la collection
            child_id = node.check_id(child)
            node = node.child(child_id)
        return node

    def get_callback(self,collection):
        """
        recupere la callback de collection
        Si elle n'est pas disponible renvoie une erreur 405 avec les methodes possibles
        """
        try:
            return getattr(collection,self.METHOD_MAP[self.method])
        except (AttributeError,KeyError):
            available_methods = []
            for meth in self.METHOD_MAP:
                if hasattr(collection,meth):
                    available_methods.append(meth)
            raise HTTPError(405,
                    header=[ ('allow',','.join(available_methods))])

    def handle(self):
        """
        gère l'appel FIXME du téléphone rose ?
        """
        try:
            #obtient l'object designé
            collection = self.get_collection()
            #recupère les données valides pour cet objet
            datas =  self.check_datas(collection)
            #recupère la vue qui va effectuer la requete
            callback = self.get_callback(collection)
            #recupere les arguments a passer a cette vue
            args = self.get_args(datas)
            return callback(*args)
        except ValidationError,e:
            raise HTTPError(400,'%s is not a valid identifier'%str(e))
        except KeyError,e:
            raise HTTPError(400,'%s parameter is required'%str(e))
        except NotFound,e:
            raise HTTPError(404,'%s not found'%(str(e)))
        except Duplicate,e:
            raise HTTPError(409,'%s already exists',str(e))


class ServiceCollectionRequest(ServiceRequest):
    #association de verbes HTTP aux methodes python
    METHOD_MAP = {
        'POST':'create',
        'GET':'list'
        }
    def get_args(self,datas):
        if self.method == 'GET':
            return (self.request.GET,)
        elif self.method == 'POST':
            return (datas,)
        return tuple()


class ServiceResourceRequest(ServiceRequest):
    METHOD_MAP = {
            'PUT':'modify',
            'GET':'get',
            'DELETE':'delete',
        }
    def __init__(self,request,path,collection):
        super(ServiceResourceRequest,self).__init__(request,path[:-1],collection)
        #extrait le dernier element du path qui sera la ressource
        self.resource_id = path[-1]

    def get_args(self,datas):
        if self.method == 'PUT':
            return (self.resource_id,datas)
        return (self.resource_id,)
    def get_collection(self):
        collection = super(ServiceResourceRequest,self).get_collection()
        #verifie l'identifiant de la resource aussi
        self.resource_id = collection.check_id(self.resource_id)
        return collection


"""

GET     /a/     a.list()
POST    /a/     a.create()

GET     /a/1    a.get(1)
DELETE  /a/1    a.delete(1)
PUT     /a/1    a.modify(1)

GET     /a/1/   a.get(1).list()
POST    /a/1/   a.get(1).create()
PUT     /a/1/b  a.get(1).mofify(b)
GET     /a/1/b  a.get(1).get(b).get()

"""
