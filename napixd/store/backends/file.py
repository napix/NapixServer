#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import cPickle as pickle

from napixd import get_path
from napixd.store.backends import BaseStore

class FSStore( BaseStore):
    def get_path(self):
        return get_path( self.__class__.__name__)

class FileStore( FSStore ):
    def __init__( self, collection, path = None ):
        path = path if path is not None else self.get_path()
        self.file_path = os.path.join( path , collection)
        try:
            data = pickle.load( open(self.file_path, 'r'))
        except IOError:
            data = {}
        super( FileStore, self).__init__( data )

    def drop( self):
        super( FileStore, self).drop()
        if os.path.isfile(self.file_path):
            os.unlink(self.file_path)

    def save(self):
        pickle.dump( self.data, open( self.file_path, 'w'))

class DirectoryStore( FSStore):
    def __init__( self, collection, path=None):
        path = path or self.get_path()
        self.dir_path = os.path.join( path, collection)

    def keys( self):
        try:
            return [ x for x in os.listdir( self.dir_path) if x[0] != '.' ]
        except OSError:
            return []

    def _fname( self, key):
        if '/' in key:
            raise ValueError, 'No / in key names'
        return os.path.join( self.dir_path, key)

    def __setitem__( self, key, value, _retry=True):
        try:
            pickle.dump( value, open( self._fname(key), 'w'))
        except IOError:
            if _retry and not os.path.isdir( self.dir_path):
                os.makedirs( self.dir_path, 0700)
                self.__setitem__( key, value, _retry = False)
            else:
                raise

    def __getitem__( self, key):
        try:
            return pickle.load( open(self._fname( key), 'r'))
        except IOError:
            raise KeyError, key
    def __delitem__( self, key):
        try:
            os.unlink( self._fname( key))
        except IOError:
            raise KeyError, key
    def drop( self):
        for key in self.keys():
            del self[key]
        try:
            os.rmdir( self.dir_path )
        except OSError:
            pass
    def incr( self, key, by=0):
        raise NotImplementedError, 'DirectoryStore does not implement incr'

