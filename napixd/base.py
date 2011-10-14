#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Collection(object):
    resource_class = None

    def delete_child(self,id):
        try:
            return self.resource_class.get(id).delete()
        except AttributeError:
            raise NotImplementedError

    def create_child(self,id,values):
        try:
            return self.resource_class.create(values)
        except AttributeError:
            raise NotImplementedError

    def list_child(self):
        try:
            return self.resource_class.list()
        except AttributeError:
            raise NotImplementedError

    def get_child(self,id):
        try:
            return dict(self.resource_class.get(id))
        except AttributeError:
            raise NotImplementedError

    def modify_child(self,id,values):
        try:
            return self.resource_class.get(id).modify(values)
        except AttributeError:
            raise NotImplementedError

    @classmethod
    def get(self,id):
        return {}
    @classmethod
    def list(self):
        return []
    @classmethod
    def create(self,values):
        pass
    def modify(self,values):
        pass
    def delete(self):
        pass
