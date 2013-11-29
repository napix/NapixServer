#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import socket

from napixd.managers.default import ReadOnlyUniqueManager


class HostInfo(ReadOnlyUniqueManager):
    """
    Dumb class that try to collect information about running host
    """

    resource_fields = {
        'hostname': {
            'description': 'Hostname of running host',
            'example': 'somehost'
        },
        'uname': {
            'description': 'uname -a of running host',
            'example': 'Linux platoon 3.7-trunk-amd64 #1 SMP Debian 3.7.8-1~experimental.1 x86_64 GNU/Linux'
        },
        'fqdn': {
            'description': 'Fully qualified name of running host',
            'example': 'somehost.somedomain.com'
        },
    }

    def load(self, parent):
        uname = subprocess.Popen(['uname', '-a'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        if uname.wait() != 0:
            raise ValueError(uname.stderr.read())

        uname_value = uname.stdout.read().strip()
        return {
            'hostname': socket.gethostname(),
            'uname': uname_value,
            'fqdn': socket.getfqdn(),
        }
