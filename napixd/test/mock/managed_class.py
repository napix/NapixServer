#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.exceptions import ValidationError
from napixd.managers.default import DictManager, ReadOnlyDictManager

TRANSLATION_TABLE = { 'the':'le', 'cat':'chat',
'eats':'mange', 'a':'une','mouse':'souris',
'sleeps':'dors'
}
STORE = {}

class Translations(DictManager):
    """Translation of words"""
    @classmethod
    def get_name(cls):
        return 't'
    resource_fields = {
            'translated' : {
                'description' : 'translation of a word',
                'example' : 'aferon'
                },
            'language' : {
                'description' : 'language in wich this word is translated',
                'example' : 'esperanto'
                } }
    def load(self,parent):
        return {
                'french':{
                    'translated':TRANSLATION_TABLE.get(parent['word']),
                    'language':'french'
                    } }
    def generate_new_id(self,resource_dict):
        return resource_dict['language']
    def save(self,parent,resources):
        STORE['translations'] = resources

    def get_resource( self, id_):
        if self.parent['word'] == 'cat':
            raise ValueError, 'I don\'t like cats'
        return super(Translations,self).get_resource(id_)

class Letters(ReadOnlyDictManager):
    """Letters of each word"""
    @classmethod
    def get_name(cls):
        return 'l'
    resource_fields = { 'letter':{
        'description':'letter of a word'
        }}
    def load(self, parent):
        return dict([(x,{'letter':x,'ord':ord(x)}) for x in parent['word']])

class Words(ReadOnlyDictManager):
    """Words of each paragrach"""
    managed_class = [Letters,Translations]
    resource_fields = { 'word':{
        'description':'A word in the story',
        }}
    @classmethod
    def get_name(cls):
        return 'w'
    def load(self, parent):
        return dict([(x,{'word':x,'length':len(x)}) for x in parent['text'].split(' ') ])

class Paragraphs(DictManager):
    """Stories of pets"""
    managed_class = Words
    resource_fields = { 'text':{
        'description':'Text of the story',
        'example':'The quick brown fox jump over the lazy dog'
        }}

    @classmethod
    def get_name(cls):
        return 'p'

    PETS = set(['mouse','cat','bird','fish'])
    def load(self,parent):
        return {
                'cat':{'text':'the cat eats'},
                'mouse':{'text':'a mouse sleeps'}
                }
    def save(self,parent,resource):
        STORE['paragraphs'] = resource
    def clean_text(self,word):
        if ' ' in word:
            raise ValidationError
        return word
    def validate_id(self,id_):
        if not id_ in self.PETS:
            raise ValidationError,'Story must be constructed about a pet'
        return id_

    def generate_new_id(self,resource_dict):
        for pet in self.PETS:
            if ' '+pet+' ' in resource_dict['text']:
                return pet
        raise ValidationError,'Story must include a valid PET'
