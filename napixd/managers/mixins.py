#!/usr/bin/env python
# -*- coding: utf-8 -*-

class AttrResourceMixin(object):
    def serialize( self, resource):
        return dict( (k, getattr(resource, k))
            for k in self.resource_fields.keys() )
