#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.managers.default import ReadOnlyDictManager


class HostManager( ReadOnlyDictManager ):

    name = 'hosts'
    resource_fields = {
            'hostnames' : {
                'description' : 'List of hostnames related to this IPs'
                },
            'ip' : {
                'description' : 'The IP of the host'
                }
            }

    def load( self, parent):
        try:
            handle = open( '/etc/hosts', 'r')
        except IOError:
            return {}

        resources = {}
        for line in map(str.strip, handle.readlines()):
            if not line or line[0] == '#':
                continue
            line = filter( bool, line.replace( '\t', ' ').split(' '))
            ip = line[0]
            hostnames = line[1:]
            resources[hostnames[1]] = {
                    'ip' : ip , 'hostnames' : hostnames
                    }
        return resources



