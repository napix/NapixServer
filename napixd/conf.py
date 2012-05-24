#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
import os.path
import UserDict


logger = logging.getLogger()

class Conf(UserDict.UserDict):
    _default = None

    paths = [ '/etc/napixd/', os.path.join( os.path.dirname(__file__), '..', 'conf') ]

    @classmethod
    def get_default(cls):
        if not cls._default:
            cls._make_default()
        return cls._default

    @classmethod
    def _make_default(cls):
        for path in cls.paths :
            path = os.path.join( path, 'settings.json')
            if os.path.isfile( path):
                conf = json.load( open( path, 'r' ))
                cls._default = cls(conf)
                return
        logger.warning( 'Did not find any configuration ')
        return cls( {} )

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

