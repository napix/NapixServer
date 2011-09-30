#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.exceptions import ValidationError

class Collection(object):
    """classe de base d'une collection"""
    def check_id(self,id_):
        if id_ ==  '':
            raise ValidationError,'ID cannot be empty'
        return id_
