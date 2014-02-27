#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

from dotconf import Dotconf
from dotconf.parser import ParsingError
from dotconf.tree import (
    ConfigValue,
    MultipleSectionsWithThisNameError,
)

from napixd import conf


class ConfFactory(object):
    def get_filename(self):
        return 'settings.conf'

    def parse_file(self, handle):
        return self.parse_string(handle.read().decode('utf-8'))

    def parse_string(self, string):
        if not string.endswith('\n'):
            string += '\n'
        try:
            dc = Dotconf(string)
            return Conf(dc.parse())
        except ParsingError as e:
            raise ValueError('At {0.position}, Cannot parse string, {0}'.format(e))


class Conf(conf.BaseConf):
    def __init__(self, section):
        self.section = section

    def __iter__(self):
        return (child.name
                if isinstance(child, ConfigValue) or not child.args else
                '{0} {1}'.format(child.name, child.args[0])
                for child in self.section.iterflatchildren())

    def __len__(self):
        keys = list(self.section.iterflatchildren())
        return len(keys)

    def __nonzero__(self):
        return len(self) != 0

    def _get_own(self, key):
        value = self.section.get(key)
        if value is not None:
            return value

        value = self._subsection(key)
        if value is not None:
            return value

        return None

    def _subsection(self, key):
        if ' ' in key:
            key, sp, arg = key.partition(' ')
        else:
            arg = None

        if arg is not None:
            for subsection in self.section.subsections(key):
                if subsection.args and subsection.args[0] == arg:
                    return Conf(subsection)
            else:
                return None

        try:
            section = self.section.subsection(key)
            if not section or section.args:
                return None
            return Conf(section)
        except MultipleSectionsWithThisNameError:
            for subsection in self.section.subsections(key):
                if not subsection.args:
                    return Conf(subsection)
            else:
                return None

    def __getitem__(self, key):
        value = self._get_own(key)
        if value is not None:
            return value

        prefix, dot, suffix = key.partition('.')
        if not dot:
            raise KeyError(key)

        if ' ' in prefix:
            prefix, dot, suffix = key.rpartition('.')

        ss = self._subsection(prefix)
        if ss is not None:
            return ss[suffix]

        raise KeyError(key)

    def __contains__(self, key):
        value = self._get_own(key)
        if value is not None:
            return True

        prefix, dot, suffix = key.partition('.')
        if not dot:
            return False

        if ' ' in prefix:
            prefix, dot, suffix = key.rpartition('.')

        ss = self._subsection(prefix)
        if ss is not None:
            return suffix in ss

        return False
