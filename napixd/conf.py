#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Conf(object):
    def __init__(self,section):
        self.section = dict(section)

    def for_manager(self,stack):
        prefix = self._get_prefix(stack)
        for key,value in self.section.items():
            if key.startswith(prefix):
                yield key[len(prefix):],value

    def get(self,stack,key,defaut):
        prefix = self._get_prefix(stack)
        return self.section.get(prefix+key,defaut)

    def _get_prefix(self,stack):
        return len(stack) > 1 and '.'.join(map(lambda x:x.get_name(),stack[1:]))+'.' or ''
