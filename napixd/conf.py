#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os.path
import UserDict


_default = None

class Conf(UserDict.UserDict):
    _default = None
    @classmethod
    def get_default(cls):
        if not cls._default:
            cls._default = Conf(json.load(
                open(os.path.join( os.path.dirname(__file__),
                    'conf','settings.json'),'r')))
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

