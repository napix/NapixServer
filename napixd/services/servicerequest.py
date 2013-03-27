#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import unquote

import bottle

from napixd.http import Response
from napixd.exceptions import NotFound,ValidationError,Duplicate

class ServiceRequest(object):
    """
    ServiceRequest is an abstract class that is created to serve a single request.
    """
    def __init__(self,path,service):
        """
        Create the object that will handle the request for the path given on the collection
        """
        self.method = bottle.request.method
        self.service = service
        #Parse the url components
        self.path = map( unquote, path)

    @classmethod
    def available_methods(cls,manager):
        """
        Return the HTTP methods defined in the given manager
        that are usable with this ServiceRequest
        """
        available_methods = []
        for meth,callback in cls.METHOD_MAP.items():
            if hasattr(manager,callback):
                available_methods.append(meth)
        return available_methods

    def check_datas(self):
        """
        Filter and check the collection fields.

        Remove any field that is not in the collection's field
        Call the validator of the collection
        """
        if self.method not in ('POST','PUT') :
            return {}
        data = {}
        for key, meta  in self.manager.resource_fields.items():
            if key in bottle.request.data:
                value = bottle.request.data[key]
            elif meta.get('optional',False) or meta.get('computed',False):
                continue
            else:
                raise ValidationError, 'Missing argument `%s`' % key
            if 'unserializer' in meta:
                value = meta['unserializer'](value)
            if 'type' in meta:
                if not isinstance( value, meta['type']):
                    raise ValidationError, 'key %s is not of type %s but type %s' %(
                            key, meta['type'].__name__, type(value).__name__)
            data[key] = value
        data = self.manager.validate(data)
        return data

    def get_manager(self):
        """
        Récupere la collection correspondante à la requete
        """
        self.all_managers, manager = self.service.get_managers(self.path)
        return manager

    def get_callback(self):
        """
        recupere la callback de manager
        Si elle n'est pas disponible renvoie une erreur 405 avec les methodes possibles
        """
        try:
            return getattr( self.manager,self.METHOD_MAP[self.method])
        except (AttributeError,KeyError):
            raise bottle.HTTPError(405, 'Method is not implemented',
                    allow= ','.join(self.available_methods( self.manager)))

    def call(self):
        """
        Make the actual call of the method
        """
        raise NotImplementedError

    def start_request( self):
        for m,i,r in self.all_managers:
            m.start_request( bottle.request)
            m.start_managed_request( bottle.request, i, r)
        self.manager.start_request( bottle.request)

    def end_request( self):
        self.manager.end_request( bottle.request)
        for m,i,r in reversed(self.all_managers):
            m.end_managed_request( bottle.request, i, r)
            m.end_request( bottle.request)

    def serialize( self, result):
        return result

    def handle(self):
        """
        Actually handle the request.
        Call a set of methods that may be overrident by subclasses
        """
        try:
            #obtient l'object designé
            self.manager = self.get_manager()
            self.start_request()

            #recupère la vue qui va effectuer la requete
            self.callback = self.get_callback()
            #recupère les données valides pour cet objet
            self.data =  self.check_datas()
            #recupere les arguments a passer a cette vue
            result = self.call()

            self.end_request()
            return self.serialize(result)
        except ValidationError,e:
            raise bottle.HTTPError(400,str(e))
        except NotFound,e:
            raise bottle.HTTPError(404,'`%s` not found'%str(e))
        except Duplicate,e:
            raise bottle.HTTPError(409,'`%s` already exists'%str(e))

    def make_url(self,result):
        url = ''
        path = list(self.path)
        path.append(result)
        for service,id_ in zip(self.service.services,path):
            url += '/'+service.get_token(id_)
        return url

class ServiceCollectionRequest(ServiceRequest):
    """
    ServiceCollectionRequest is an implementation of ServiceRequest specified for Collection requests (urls ending with /)
    """
    #association de verbes HTTP aux methodes python
    METHOD_MAP = {
        'POST':'create_resource',
        'GET':'list_resource',
        'HEAD' : 'list_resource'
        }
    def call(self):
        if self.method == 'POST':
            return self.callback(self.data)
        else:
            return self.callback()

    def serialize( self, result):
        if self.method == 'HEAD':
            return None
        elif self.method == 'POST':
            url = self.make_url(result)
            return bottle.HTTPError(201, None, Location= url)
        elif self.method == 'GET':
            return map(self.make_url,result)
        else:
            return result

class ServiceResourceRequest(ServiceRequest):
    """
    ServiceResourceRequest is an implementation of ServiceRequest specified for Ressource requests (urls not ending with /)
    """
    METHOD_MAP = {
            'PUT':'modify_resource',
            'GET':'get_resource',
            'HEAD' : 'get_resource',
            'DELETE':'delete_resource',
        }

    def serialize( self, result):
        if self.method == 'HEAD':
            return None
        if self.method == 'PUT' and result != None :
            new_url = self.make_url(result)
            if new_url != bottle.request.path:
                return bottle.HTTPError(303, None, Location= new_url )
            return None
        if self.method != 'GET':
            return result
        format_ = bottle.request.GET.get('format', None )
        if not format_:
            return self.default_formatter( result)
        try:
            formatter = self.manager.get_formatter( format_)
        except KeyError:
            message = 'Cannot render %s.' % format_
            all_formats = self.service.collection.get_all_formats()
            if all_formats:
                message = '{0} Available formats {1}: {2} '.format(
                        message, 'is' if len( all_formats) <= 1 else 'are',
                        ','.join(all_formats.keys()))
            return bottle.HTTPError( 406, message)

        response = Response()
        result = formatter( self.resource_id, result, response)
        if result is None or result is response:
            return response
        else:
            return result

    def default_formatter(self, value):
        resp = self.manager.serialize( value )
        for key,meta in self.manager.resource_fields.items():
            if callable(meta.get('serializer')):
                resp[key] = meta['serializer'](resp[key])
        return resp

    def call(self):
        if self.method == 'PUT':
            return self.callback(self.resource_id, self.data)
        else:
            return self.callback( self.resource_id)

    def get_manager(self):
        #get the last path token because we may not just want to GET the resource
        resource_id = self.path.pop()
        manager = super(ServiceResourceRequest,self).get_manager()
        #verifie l'identifiant de la resource aussi
        self.resource_id = manager.validate_id(resource_id)
        return manager

class ServiceActionRequest(ServiceResourceRequest):
    METHOD_MAP = {
            'POST' : 'get_resource',
        }
    def __init__(self, path, service, action_name):
        self.action_name = action_name
        super(ServiceActionRequest,self).__init__(path, service)

    def get_callback(self):
        self.resource = self.manager.get_resource(self.resource_id)
        return getattr( self.manager, self.action_name)

    def check_datas(self):
        callback = getattr(self.manager, self.action_name)
        supplied = set(bottle.request.data.keys())
        if not supplied.issuperset(callback.mandatory):
            raise ValidationError, 'missing mandatory parameters %s'%(
                    ','.join(set(callback.mandatory ).difference( supplied)))
        data = {}
        for key in callback.all_parameters.intersection(supplied):
            data[key] = bottle.request.data[key]
        return data

    def call(self):
        return self.callback(self.resource, **self.data)
