#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
import os.path
import UserDict
import napixd
from contextlib import contextmanager

logger = logging.getLogger('Napix.conf')

#So that it's overridable in the tests
open = open

class Conf(UserDict.UserDict):
    _default = None

    paths = [
            '/etc/napixd/',
            napixd.get_path( 'conf'),
            os.path.join( os.path.expanduser('~'), '.napix')
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
        for path in cls.paths :
            path = os.path.join( path, 'settings.json')
            try:
                handle = open( path, 'r' )
                if conf:
                    logger.warning('Stumbled upon configuration file candidate %s,'+
                            ' but conf is already loaded', path)
                    continue
                logger.info( 'Using %s configuration file', path)
                conf = json.load( handle )
            except ValueError, e:
                logger.error('Configuration file %s contains a bad JSON object (%s)', path, e)
            except IOError:
                pass

        if not conf:
            logger.warning( 'Did not find any configuration, trying default conf')
            try:
                conf = json.load( open( 'default_conf/settings.json'))
            except IOError:
                logger.error( 'Did not find any configuration at all')
                conf = {}

        cls._default = cls( conf )
        return cls._default

    def __getitem__( self, item):
        if '.' in item :
            prefix, x, suffix = item.rpartition('.')
            return self.get(prefix)[suffix]
        else:
            return self.data[item]

    def __delitem__(self, item):
        if '.' in item :
            prefix, x, suffix = item.rpartition('.')
            cont = self[prefix]
            del cont[suffix]
            if not cont:
                del self[prefix]
        else:
            del self.data[item]

    def __nonzero__(self):
        return bool(self.data)

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

