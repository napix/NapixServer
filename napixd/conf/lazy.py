#!/usr/bin/env python
# -*- coding: utf-8 -*-


from napixd.conf import BaseConf, Conf


class LazyConf(BaseConf):
    def __init__(self, key, source=Conf):
        self._key = key
        self._source = source

    @property
    def _value(self):
        value = self.__dict__['_value'] = self._source.get_default(self._key)
        return value

    def __iter__(self):
        return iter(self._value)

    def __len__(self):
        return len(self._value)

    def __getitem__(self, key):
        return self._value[key]

    def __getattribute__(self, name):
        if name.startswith('_'):
            if name == '__dict__':
                return super(LazyConf, self).__getattribute__(name)

            if name in self.__dict__:
                return self.__dict__[name]
            return super(LazyConf, self).__getattribute__(name)

        return getattr(self._value, name)
