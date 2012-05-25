#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
import os.path
import UserDict

logger = logging.getLogger('Napix.conf')

class Conf(UserDict.UserDict):
    _default = None

    paths = [ '/etc/napixd/', os.path.realpath( os.path.join( os.path.dirname(__file__), '..', 'conf')) ]

    @classmethod
    def get_default(cls):
        if not cls._default:
            cls._make_default()
        return cls._default

    @classmethod
    def _make_default(cls):
        conf = None
        for path in cls.paths :
            path = os.path.join( path, 'settings.json')
            if os.path.isfile( path):
                if conf:
                    logger.warning('Stumbled upon configuration file candidate %s,'+
                            ' but conf is already loaded', path)
                    continue
                logger.info( 'Using %s configuration file', path)
                try:
                    conf = json.load( open( path, 'r' ))
                except ValueError:
                    logger.error('Configuration file contains a bad JSON object')
        if not conf:
            logger.warning( 'Did not find any configuration')
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
            return Conf( self[section_id] )
        except (KeyError,ValueError):
            return Conf()

