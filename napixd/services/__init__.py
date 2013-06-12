#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from urllib import quote

import sys

from napixd.conf import Conf
from napixd.services.servicerequest import (ServiceCollectionRequest,
        ServiceResourceRequest, ServiceActionRequest)
from napixd.services.plugins import ArgumentsPlugin

"""
The service class ack like a proxy between bottle and napix resource Manager Component.

It handles bottle registering, url routing and Manager configuration when needed.
"""
logger = logging.getLogger('Napix.service')

def urlencode(string):
    #like quote but alse encode the /
    return quote( string, '')

class Service(object):
    """
    The service objects make the interface between the end user's HTTP calls and the active modules.
    """
    def __init__(self, collection, namespace = None, configuration = None ):
        """
        Create a base service for the given collection and its managed classes.
        collection MUST be a Manager subclass and configuration an instance of Conf
        for this collection
        """
        self.configuration = configuration or Conf()
        self.collection_services = []
        self.url = namespace or collection.get_name()

        service = FirstCollectionService( collection, self.configuration, self.url)
        self._append_service( service)
        self.create_collection_service( collection, service )

    def _append_service( self, service):
        self.collection_services.append(service)

    def make_collection_service( self, previous_service, managed_class, namespace ):
        config_key = '{0}.{1}'.format( previous_service.get_name(), namespace or managed_class.get_name() )
        service = CollectionService(
                previous_service,
                managed_class,
                self.configuration.get( config_key),
                namespace)
        self._append_service( service )
        self.create_collection_service( managed_class.manager_class, service)

    def create_collection_service(self, collection, previous_service ):
        if collection.direct_plug() != None:
            for managed_class in collection.get_managed_classes():
                self.make_collection_service(
                        previous_service,
                        managed_class,
                        managed_class.get_name() if not collection.direct_plug() else '' )

    def setup_bottle(self,app):
        """
        Route the managers inside the given bottle app.
        """
        logger.debug( 'Setting %s', self.url )
        for service in self.collection_services:
            service.setup_bottle(app)

class BaseCollectionService(object):

    collection_request_class = ServiceCollectionRequest
    resource_request_class = ServiceResourceRequest

    def __init__(self, previous_service, collection, config, namespace):
        """
        Serve the collection given as a managed class of the previous_service, with the config given.
        collection is a subclass of Manager
        previous_service is an instance of CollectionService that serve the Manager class below.
        previous_service is None when it's the base collection being served.
        config is the instance of Conf for this Service.
        append_url is a boolean that add the URL token between the previous and this service.
        """
        self.previous_service = previous_service
        self.collection = collection
        self.config = config

        #Recursive list of services.
        self.services = list(self._services_stack())
        self.services.reverse()

        self.direct_plug = self.collection.direct_plug()
        #url is added if append_url is True
        self.url = namespace

        base_url = '/'
        last = len(self.services) -1
        #build the prefix url with the list of previous services
        for i,service in enumerate(self.services):
            base_url += service.get_prefix()
            if i != last:
                base_url += ':f%i/'%i
        #collection and resource urls of this service
        self.collection_url = base_url
        self.resource_url = base_url + ':f%i' % last

        self.all_actions = list(self.collection.get_all_actions())

        self.resource_fields = dict( (x,dict(y)) for x,y in self.collection.resource_fields.items())
        for field, field_meta in self.resource_fields.items():
            validation_method = getattr( self.collection, 'validate_resource_' + field, None)
            if hasattr( validation_method, '__doc__') and validation_method.__doc__ is not None:
                field_meta['validation'] = validation_method.__doc__
            else:
                field_meta['validation'] = ''

            for callable_ in ( 'unserializer', 'serializer', 'type'):
                if callable_ in field_meta:
                    if field_meta[callable_] in ( str, basestring, unicode):
                        field_meta[callable_] = 'string'
                    else:
                        field_meta[callable_] = field_meta[callable_].__name__

    def get_name(self):
        return '.'.join( s.url for s in self.services)

    def get_prefix(self):
        """
        Get the prefix of this service
        if append_url was True, this service hasn't a prefix
        else, it's the url from the configuration
        ex:
        >>>cs = CollectionService(ps,ManagerClass,conf,namespace)
        >>>cs.get_prefix()
            'managerclass/'

        >>>cs = CollectionService(ps,ManagerClass,conf,namespace)
        >>>cs.get_prefix()
            ''
        """
        return self.url and self.url + '/' or ''
    def get_token(self,path):
        """
        get the url bit for a resource identified by path for this collection
        """
        return self.get_prefix()+urlencode(str(path))

    def get_managers( self, path):
        resource = {}
        #self.services is one item shorter than path and that item is self
        #Thus we search in the path for each of the ancestors of self
        #but not for self.
        managers_list = []
        for id_,service in zip( path, self.services):
            manager = service.generate_manager(resource)
            id_ = manager.validate_id( id_ )
            resource = manager.get_resource( id_ )
            managers_list.append( ( manager, id_, resource) )
        #The manager for self is generated here.
        manager = self.generate_manager( resource)
        return managers_list, manager

    def generate_manager(self,resource):
        """
        instanciate a manager for the given resource
        """
        manager = self.collection(resource)
        manager.configure(self.config)
        return manager

    def _services_stack(self):
        """
        return the list of services before this one
        """
        serv = self
        yield serv
        while serv.previous_service:
            yield serv.previous_service
            serv = serv.previous_service

    def setup_bottle(self,app):
        """
        Register the routes of this collection inside the app
        collection/                         list the collection
        collection/_napix_new               New object template
        collection/_napix_help              collection complete documentation
        collection/_napix_resource_fields   collection resource files documentation

        collection/resource                         Get the specified resource
        collection/resource/_napix_all_actions      All actions of the resource

        collection/resource/_napix_action/action                Call the action on the resource
        collection/resource/_napix_action/action/_napix_help    documentation of the action
        """
        arguments_plugin = ArgumentsPlugin()
        app.route(self.collection_url+'_napix_resource_fields',callback=self.as_resource_fields,
                method='GET',apply=arguments_plugin)
        app.route(self.collection_url+'_napix_help',callback=self.as_help,
                method='GET',apply=arguments_plugin)
        if hasattr(self.collection, 'create_resource'):
            app.route(self.collection_url+'_napix_new',callback=self.as_example_resource,
                    method='GET',apply=arguments_plugin)
        if self.all_actions:
            app.route(self.resource_url+'/_napix_all_actions',callback=self.as_list_actions,
                    method='GET',apply=arguments_plugin)
        for action in self.all_actions:
            app.route( self.resource_url+'/_napix_action/'+action.__name__ +'/_napix_help',
                    method='GET', callback = self.as_help_action_factory(action),
                    apply = arguments_plugin)
            app.route( self.resource_url+'/_napix_action/'+action.__name__ , method='POST',
                    callback = self.as_action_factory(action.__name__ ),
                    apply = arguments_plugin)
        app.route(self.collection_url,callback=self.as_collection,
                method='ANY',apply=arguments_plugin)
        app.route(self.resource_url,callback=self.as_resource,
                method='ANY',apply=arguments_plugin)

        if self.direct_plug == False :
            app.route(self.resource_url+'/',
                    callback = self.as_managed_classes , apply = arguments_plugin)
            for managed_class in self.collection.get_managed_classes():
                app.route( self.resource_url + '/' + managed_class.get_name(), callback=self.noop)

    def as_resource(self,path):
        return ServiceResourceRequest( path, self).handle()

    def as_collection(self,path):
        return ServiceCollectionRequest( path, self).handle()

    def as_action_factory(self,action_name):
        def as_action(path):
            return ServiceActionRequest(path, self, action_name).handle()
        return as_action

    def as_help_action_factory(self,action):
        def as_help_action(path):
            return {
                    'resource_fields' : action.resource_fields,
                    'doc' : action.__doc__,
                    'mandatory': action.mandatory,
                    'optional' : action.optional
                    }
        return as_help_action

    def make_urls(self, path, all_urls):
        url = ''
        for service,id_ in zip(self.services,path):
            url += '/'+ service.get_token(id_)
        return [ '%s/%s'%(url,urlencode(name)) for name in all_urls ]

    def as_list_actions(self,path):
        return [ x.__name__ for x in self.all_actions ]

    def as_managed_classes(self,path):
        all_urls = list(x.get_name() for x in self.collection.get_managed_classes())
        if self.all_actions:
            all_urls.append('_napix_all_actions')
        return self.make_urls(path, all_urls)

    def as_help( self, path):
        manager = self.collection
        return {
                'doc' : (manager.__doc__ or '').strip(),
                'direct_plug' : self.direct_plug,
                'views' : dict( (format_, (cb.__doc__ or '').strip())
                    for (format_,cb) in self.collection.get_all_formats().items() ),
                'managed_class' : [ mc.get_name() for mc in self.collection.get_managed_classes() ],
                'actions' : dict( ( action.__name__, (action.__doc__ or '').strip())
                    for action in self.all_actions ),
                'collection_methods' : ServiceCollectionRequest.available_methods(manager),
                'resource_methods' : ServiceResourceRequest.available_methods(manager),
                'resource_fields' : self.resource_fields,
                'source' : {
                    'class' : self.collection.__name__,
                    'module' : self.collection.__module__,
                    'file' : sys.modules[ self.collection.__module__].__file__,
                    },
                }

    def as_resource_fields(self,path):
        return self.resource_fields

    def as_example_resource(self,path):
        manager = self.collection
        return manager.get_example_resource()

    def noop(self, **kw):
        return None

class FirstCollectionService(BaseCollectionService):
    def __init__(self, collection, config, namespace):
        super(FirstCollectionService, self).__init__( None, collection, config, namespace)
        self._cache = None

    def generate_manager( self, resource):
        if self._cache is None or not self._cache.is_up_to_date():
            self._cache = super(FirstCollectionService, self).generate_manager(resource)
        return self._cache

    def setup_bottle( self, app):
        app.route( '/'+self.url, callback = self.noop)
        super( FirstCollectionService, self).setup_bottle(app)

class CollectionService( BaseCollectionService):
    def __init__(self, previous_service, managed_class, config, namespace):
        super( CollectionService, self).__init__( previous_service, managed_class.manager_class, config, namespace)
        self.extractor = managed_class.extractor

    def generate_manager(self,resource):
        """
        instanciate a manager for the given resource
        """
        resource = self.extractor( resource)
        return super( CollectionService, self).generate_manager( resource)
