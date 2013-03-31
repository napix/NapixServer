#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The napix Configuration class.
"""


import logging
import json
import os.path
import collections
import napixd
from contextlib import contextmanager

logger = logging.getLogger('Napix.conf')

#So that it's overridable in the tests
open = open

class Conf(collections.MutableMapping):
    _default = None
    def __init__(self, data=None):
        self.data = dict(data) if data else {}

    def __repr__(self):
        return repr(self.data)

    def __iter__(self):
        return ( key for key in self.data if not key.startswith('#') )
    def iteritems(self):
        return ( (key,value) for key,value in self.data.items() if not key.startswith('#') )
    def __len__(self):
        return len(self.data)

    paths = [
            napixd.get_file( 'conf/settings.json'),
            '/etc/napixd/settings.json',
            ]

    @classmethod
    def get_default(cls, value = None):
        if cls._default is None:
            cls.make_default()
        if value is None:
            return cls._default
        else:
            return cls._default.get(value)

    @classmethod
    def make_default(cls):
        conf = None
        paths = iter( cls.paths)
        for path in paths:
            try:
                handle = open( path, 'r' )
                logger.info( 'Using %s configuration file', path)
            except IOError:
                pass
            else:
                try:
                    conf = json.load( handle )
                    break
                except ValueError, e:
                    raise ValueError('Configuration file %s contains a bad JSON object (%s)'%( path, e))
                finally:
                    handle.close()
        else:
            try:
                default_conf = os.path.join( os.path.dirname(__file__), 'settings.json' )
                logger.warning( 'Did not find any configuration, trying default conf from %s', default_conf)
                with open( default_conf, 'r') as handle:
                    conf = json.load(handle)
                for path in cls.paths :
                    try:
                        logger.info('Try to write default conf to %s', path)
                        with open( path, 'w') as destination:
                            with open(default_conf, 'r') as source:
                                destination.write(source.read())
                    except IOError:
                        logger.warning('Failed to write conf in %s', path)
                    else:
                        logger.info('Conf written to %s', path)
                        break
                else:
                    logger.error('Cannot write defaulf conf')
            except IOError:
                logger.error( 'Did not find any configuration at all')
                conf = {}

        cls._default = cls( conf )
        return cls._default

    def __getitem__( self, item):
        if item in self.data:
            return self.data[item]
        if '.' in item :
            prefix, x, suffix = item.partition('.')
            base = self[prefix]
            if isinstance( base, dict):
                return Conf(base)[suffix]
        raise KeyError, item

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, item):
        if '.' in item :
            prefix, x, suffix = item.rpartition('.')
            cont = self[prefix]
            del cont[suffix]
            if not cont:
                del self[prefix]
        else:
            del self.data[item]

    def __contains__(self, item):
        if not self:
            return False
        if item in self.data:
            return True
        if '.' in item :
            prefix, x, suffix = item.partition('.')
            return suffix in self.get(prefix)
        return False

    def __nonzero__(self):
        return bool(self.data)

    def __eq__(self, other):
        return  isinstance( other, collections.Mapping) and other.keys() == self.keys() and other.values() == self.values()

    def get( self, section_id):
        try:
            value = self[section_id]
        except (KeyError,ValueError):
            return Conf()
        if isinstance( value, dict):
            return Conf(value)
        return value

    def _set(self, item, value):
        self._do_set( self.data, item, value)

    def _do_set(self, dataset, item, value):
        if '.' in item :
            prefix, x, suffix = item.partition('.')
            self._do_set( dataset.setdefault( prefix, {}), suffix, value )
        else:
            dataset[item] = value

    @contextmanager
    def force(self, param, value):
        old_value = self.get( param)
        self._set( param, value)
        yield
        if old_value:
            self._set( param, old_value)
        else:
            del self[param]

