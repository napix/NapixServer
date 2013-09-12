#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.managers.base import Manager
from napixd.exceptions import ValidationError


class HelloWorld(Manager):
    resource_fields = {
        'hello': {
            'description': 'Say hello',
            'example': 'world',
        }
    }

    def validate_id(self, id):
        if id != 'world':
            raise ValidationError('id is world')
        return id

    def list_resource(self):
        return ['world']

    def get_resource(self, id):
        return {"hello": "world"}


class ConfiguredHelloWorld(HelloWorld):

    def is_up_to_date(self):
        return True

    def configure(self, conf):
        self.msg = conf.get('hello') or 'world'

    def get_resource(self, id):
        return {"hello": self.msg}
