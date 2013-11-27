#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.managers.default import ReadOnlyDictManager


class HostManager(ReadOnlyDictManager):
    """
    Read only manager for the /etc/hosts file.
    """

    name = 'hosts'
    resource_fields = {
        'hostnames': {
            'example': 'localhost',
            'description': 'List of hostnames related to this IPs'
        },
        'ip': {
            'example': '127.0.0.1',
            'description': 'The IP of the host'
        }
    }

    def load(self, parent):
        try:
            handle = open('/etc/hosts', 'r')
        except IOError:
            return {}

        resources = {}
        for line in handle:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            line = line.split()
            ip = line[0]
            hostnames = line[1:]
            resources[hostnames[1]] = {
                'ip': ip,
                'hostnames': hostnames,
            }
        return resources
