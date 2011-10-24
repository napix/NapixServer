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
    Bottle only passes the arguments from the url by keyword.

    This bottle plugin get the dict provided by bottle and get it in a tuple form

    url: /plugin/:f1/:f2/:f3
    bottle args : { f1:path1, f2:path2, f3:path3 }
    after plugin: (path1,path2,path3)
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
                #limit to keywords given in the kwargs
                itertools.takewhile(lambda x:x in kw,
                    #infinite generator of f0,f1,f2,...
                    itertools.imap(lambda x:'f%i'%x,
                        #infinite generator of 0,1,2,3...
                        itertools.count())))

class Service(object):
    """Class qui sert d'interface entre une application bottle et les collections
    FIXME : c'est la classe qui est déstinée a être overrider, le préciser."""
    def __init__(self,collection,config):
        """crée un nouveau service pour la collection donnée"""
        self.url = 'url' in config and config['url'] or collection.__name__.lower()
        collection.configure(config)
        self.collection = collection({})

    def setup_bottle(self,app):
        """Enregistre le service sur l'application bottle passée"""
        self._setup_bottle(app,self.collection,'/'+self.url,0)

    def _setup_bottle(self,app,collection,prefix,level):
        """Fonction récursive pour enregister une collection et ses sous-collections"""
        app.route('%s'%(prefix),method='ANY',callback=self.as_resource,apply=ArgumentsPlugin)
        next_prefix = '%s/:f%i'%(prefix,level)
        app.route('%s/'%(prefix),method='ANY',callback=self.as_collection,apply=ArgumentsPlugin)
        if hasattr(collection,'managed_class'):
            self._setup_bottle(app,collection.resource_class,next_prefix,level+1)

    def as_resource(self,request,path):
        """Callback appellé pour une requete demandant une collection"""
        return ServiceResourceRequest(request,path,
                self.collection).handle()

    def as_collection(self,request,path):
        """Callback appellé pour une requete demandant une resource"""
        return ServiceCollectionRequest(request,path,
                self.collection).handle()

    def as_example_resource(self,request,path):
        return None

    def as_help(self,request,path):
        return None

class ServiceRequest(object):
    """
    ServiceRequest is an abstract class that is created to serve a single request.
    """
    def __init__(self,request,path,collection):
        """
        Create the object that will handle the request for the path given on the collection
        """
        self.request = request
        self.method = request.method
        self.base_collection = collection
        self.path = path

    def check_datas(self,collection):
        """
        Filter and check the collection fields.

        Remove any field that is not in the collection's field
        Call the validator of the collection
        """
        data = {}
        for x in self.request.data:
            if x in collection.resource_fields:
                data[x] = self.request.data[x]
        data = collection.validate_resource(data)
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
        Actually handle the request.
        Call a set of methods that may be overrident by subclasses
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
    """
    ServiceCollectionRequest is an implementation of ServiceRequest specified for Collection requests (urls ending with /)
    """
    #association de verbes HTTP aux methodes python
    METHOD_MAP = {
        'POST':'create_resource',
        'GET':'list_resource'
        }
    def get_args(self,datas):
        if self.method == 'POST':
            return (datas,)
        return tuple()


class ServiceResourceRequest(ServiceRequest):
    """
    ServiceResourceRequest is an implementation of ServiceRequest specified for Ressource requests (urls not ending with /)
    """
    METHOD_MAP = {
            'PUT':'modify_resource',
            'GET':'get_resource',
            'DELETE':'delete_resource',
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
