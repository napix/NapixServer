#!/usr/bin/env python
# -*- coding: utf-8 -*-


from napixd.managers import Manager

SEEN = None

class Players(Manager):
    resource_fields = {
            'name' : {
                'type' : str
                },
            'score' : {
                'serializer' : lambda x: format( x, '.2f'),
                'unserializer' : float
                },
            'team' : {
                'optional' : True,
                'type' : str
                }
            }

    def create_resource( self, resource_dict):
        name = type( resource_dict['name']).__name__
        score = type( resource_dict['score']).__name__
        team = type( resource_dict['team']).__name__ if 'team' in resource_dict else ''
        return name + '-' + score + '-' + team

    def list_resource( self):
        return [ 1 ]

    def get_resource( self,id_):
        return {
                'name' : 'McKayla Maroney',
                'score' : 15.300,
                'team' : 'USA'
                }
