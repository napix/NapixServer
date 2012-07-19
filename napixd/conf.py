#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
import os.path
import UserDict
import napixd

logger = logging.getLogger('Napix.conf')

class Conf(UserDict.UserDict):
    _default = None

    paths = [
            '/etc/napixd/',
            os.path.realpath( os.path.join( napixd.HOME, 'conf')),
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

    def get( self, section_id):
        try:
            value = self[section_id]
        except (KeyError,ValueError):
            return Conf()
        if isinstance( value, dict):
            return Conf(value)
        return value
