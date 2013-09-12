#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.exceptions import ValidationError
from napixd.managers.default import ReadOnlyDictManager, DictManager


class HostFiles(ReadOnlyDictManager):

    """
    Host Files manager
    """
    managed_class = 'HostManager'
    resource_fields = {
        'file': {
            'example': '/etc/hosts',
            'description':
            'Path of the hosts file'
        }
    }

    def load(self, parent):
        return {
            '1': {
                'file': '/tmp/hosts1'
            },
            '2': {
                'file': '/tmp/hosts2'
            }
        }


class HostManager(DictManager):

    """
    Hosts manager
    """
    resource_fields = {
        'hostnames': {
            'description': 'List of hostname resolving to that IP',
            'example': ['localhost', 'localhost.localdomain'],
            'type': list,
        },
        'line': {
            'computed': True
        },
        'ip': {
            'description': 'IP of the host',
            'example': u'127.0.0.1',
            'type': unicode,
            'display_order': 10,
            'editable': False,
        }
    }

    def list_resource_filter(self, filters):
        ips = filters.getall('ip')
        return set(self.resources.keys()).intersection(ips)

    def validate_resource_hostnames(self, hostname):
        """
        Check that the hostname are a list of strings
        """
        if not all(isinstance(x, unicode) for x in hostname):
            raise ValidationError('hostname must be a list of strings')
        return hostname

    def validate_resource_ip(self, proposed_ip):
        """
        Check if an IP submitted by the user in his request is valid
        """
        ip_components = proposed_ip.split('.')
        if len(ip_components) != 4:
            # 123.45.67 is not an ip
            raise ValidationError('Not an ip 1')
        try:
            ip_components = map(int, ip_components)
        except ValueError:
            # 123.45.lol.99 is not an ip
            raise ValidationError('Not an ip 2')
        if not all([0 <= x <= 255 for x in ip_components]):
            # 123.45.67.890 is not an ip
            raise ValidationError('Not an ip 3')
        # filter the useless 0 out of 123.045.012.001
        return '.'.join(map(str, ip_components))

    def load(self, parent):
        """
        Load the definitions of hosts and IP

        return a dict of IP keys and list of hostnames values
        """
        try:
            file_ = open(parent['file'], 'r')
            lines = [(lineno, line.replace('\t', ' ').split(' '))
                     for lineno, line
                     in enumerate(map(str.strip, file_.readlines()))
                     if line and line[0] != '#']
        except IOError:
            lines = []

        hosts = {}
        for lineno, line in lines:
            ip = line[0]
            # remove empty strings
            hostnames = filter(bool, line[1:])
            if not ip in hosts:
                hosts[ip] = {
                    'hostnames': [],
                    'ip': ip,
                    'line': []
                }
            hosts[ip]['line'].append(lineno + 1)
            hosts[ip]['hostnames'].extend(hostnames)
        return hosts

    def generate_new_id(self, resource_dict):
        """
        resources are indexed by IP
        """
        return resource_dict['ip']

    def save(self, parent, resources):
        """
        Write the host files to the disk
        """
        file_ = open(parent['file'], 'w')
        for resource in resources.values():
            file_.write(resource['ip'])
            file_.write('\t')
            file_.write(' '.join(resource['hostnames']))
            file_.write('\n')
