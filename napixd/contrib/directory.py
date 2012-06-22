#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from napixd.managers import Manager
from napixd.exceptions import NotFound, ValidationError
from napixd.store import Store

class NapixDirectoryManager(Manager):
    """
    Keep a list of napix managers
    """

    resource_fields = {
            'host' : {
                'description' : 'The server that hosts the napix',
                'example' : 'server.napix.com'
                },
            'managers' : {
                'description' : 'the list of managers',
                'example' : [ 'directory' ]
                },
            'last_seen' : {
                'description' : 'The last time it was seen',
                'computed' : True
                },
            'status' : {
                'description' : 'OK if this server has notified recently, '
                'WAITING if it is late of less than a period, '
                'LOST after for ten periods',
                'computed' : True
                }
            }

    name = 'directory'
    TICK = 300

    def __init__(self, parent):
        super( NapixDirectoryManager, self).__init__(parent)
        self.store = Store( 'directory', backend='FileStore')

    def validate_resource_managers(self, managers):
        if ( not isinstance( managers, list) or
                not all( isinstance( x, basestring) for x in managers)) :
            raise ValidationError, ' managers should be a list of strings'
        return managers

    def get_resource(self, id_):
        try:
            resource = self.store[ id_ ]
        except KeyError:
            raise NotFound, id_
        delay =  time.time() - resource['last_seen']
        periods = delay / self.TICK
        if periods <= 1:
            resource['status'] = 'OK'
        elif periods <= 2:
            resource['status'] = 'WAITING'
        elif periods <= 10:
            resource['status'] = 'LOST'
        else:
            del self.store[id_]
            self.store.save()
            raise NotFound, id_

        return resource

    def list_resource( self):
        max_delay = self.TICK * 10
        dirty = False
        for key in list(self.store.keys()):
            if self.store[key]['last_seen'] < max_delay :
                del self.store[key]
                dirty = True
        if dirty:
            self.store.save()
        return self.store.keys()

    def modify_resource( self, id_, resource_dict):
        resource_dict['last_seen'] = time.time()
        self.store[id_] = resource_dict
        self.store.save()

    def generate_new_id(self, resource_dict):
        host = resource_dict['host']
        host = host.replace(':', '-')
        return host

    def create_resource( self, resource_dict):
        resource_dict['last_seen'] = time.time()
        id_ = self.generate_new_id( resource_dict )
        self.store[id_] = resource_dict
        self.store.save()
        return id_
