#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json

from napixd import conf


class ConfLoader(conf.ConfLoader):
    def __init__(self, paths):
        super(ConfLoader, self).__init__(paths, 'settings.json')

    def parse_file(self, handle):
        try:
            return json.load(handle)
        except ValueError, e:
            raise ValueError(
                'Configuration file contains a bad JSON object ({0})'.format(e))
