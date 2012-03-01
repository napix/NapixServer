#!/usr/bin/env python
# -*- coding: utf-8 -*-

from UserDict import IterableUserDict
import os
import cPickle as pickle
from .conf import Conf

class FileStore( IterableUserDict):
    def __init__( self, collection, path = None ):
        path = path != None and path or self.get_path() 
        self.file_path = os.path.join( path , collection)
        if not os.path.isdir( path):
            os.makedirs( path, 0700)

        try:
            self.data = pickle.load( open(self.file_path, 'r'))
        except IOError:
            self.data = {}

    def save(self):
        pickle.dump( self.data, open( self.file_path, 'w'))

    def get_path(self):
        return Conf.get_default().get( 'Napix.Store' ).get( 'path') or '/var/lib/napix'


try:
    import redis
    class RedisStore( IterableUserDict):
        def get_default_options( self):
            return Conf.get_default().get( 'Napix.Store').get('redis') or {}
        def __init__( self, collection, options= None):
            options = options != None and options or self.get_default_options()
            self.redis = redis.Redis( **options )
            self.collection = collection
            data = self.redis.get( collection)
            self.data = pickle.loads( data ) if data else {}

        def save( self):
            self.redis.set( self.collection, pickle.dumps( self.data ))
except ImportError:
    pass
