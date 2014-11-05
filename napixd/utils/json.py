#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json
from decimal import Decimal


class fakefloat(float):
    def __init__(self, decimal):
        self.decimal = decimal

    def __repr__(self):
        return str(self.decimal)


class DecimalJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return fakefloat(o)
        return super(DecimalJSONEncoder, self).default(o)


class JSONProvider(object):
    def __init__(self, pprint, decimal):
        self.cls = DecimalJSONEncoder if decimal else json.JSONEncoder
        self.indent = 4 if pprint else None
        self.parse_float = Decimal if decimal else float

    def dumps(self, value, **kw):
        kw.setdefault('cls', self.cls)
        kw.setdefault('indent', self.indent)
        return json.dump(value, **kw)

    def loads(self, value, **kw):
        return json.loads(value, parse_float=self.parse_float)
