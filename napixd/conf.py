#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

_default = None

class Conf(dict):
    _default = None
    @classmethod
    def get_default(cls):
        if not cls._default:
            cls._default = Conf(json.load(
                    open('/home/cecedille1/enix/napix/server/napixd/conf/settings.json','r')))
        return cls._default

    def for_manager(self,stack):
        prefix = self._get_prefix(stack)
        for key,value in self.items():
            if key.startswith(prefix):
                yield key[len(prefix):],value

    def _get_prefix(self,stack):
        return len(stack) > 1 and '.'.join(map(lambda x:x.get_name(),stack[1:]))+'.' or ''

    def get(self,section_id):
        try:
            return Conf( self[section_id] )
        except KeyError:
            return Conf()

