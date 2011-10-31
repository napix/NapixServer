#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.managers.default import ReadOnlyDictManager,DictManager,ListManager

class MockReadOnlyDictManager(ReadOnlyDictManager):
    resource_fields = {
            'french':{'description':'Francais'},
            'german':{'description':'Deutsh'}
            }
    def load(self,parent):
        return {
                'one':{'french':'un','german':'eins'},
                'two':{'french':'deux','german':'zwei'},
                'three':{'french':'trois','german':'drei'}
                }

class MockDictManager(DictManager):
    resource_fields = {
            'english':{'description':'English'},
            'french':{'description':'Francais'},
            'german':{'description':'Deutsh'}
            }
    def load(self,parent):
        return {
                'one':{'french':'un','german':'eins','english':'one'},
                'two':{'french':'deux','german':'zwei','english':'two'},
                'three':{'french':'trois','german':'drei','english':'three'}
                }
    def generate_new_id(self,resource_dict):
        return resource_dict['english']
    def save(self,parent,resources):
        pass

class MockListManager(ListManager):
    def load(self,parent):
        return [
               {'french':'un','german':'eins','english':'one'},
               {'french':'deux','german':'zwei','english':'two'},
               {'french':'trois','german':'drei','english':'three'}
               ]
    def save(self):
        pass

