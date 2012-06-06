#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.exceptions import ValidationError
from napixd.managers.default import DictManager

class HostManager(DictManager):
    """
    Napix Web service to manage the content of the hosts file
    """
    FILE_PATH  = '/etc/hosts'
    resource_fields = {
            'hostnames':{
                'description':'List of hostname resolving to that IP',
                'example':['localhost','localhost.localdomain']
                },
            'ip':{
                'description':'IP of the host',
                'example':'127.0.0.1'
                }
            }

    def load( self, parent ):
        #open the hosts file and keep a copy
        handle = open( self.FILE_PATH, 'rb')
        self.lines = handle.readlines()
        handle.close()
        resources = {}
        for lineno, line_content in enumerate( map( str.strip, self.lines ), 1):
            #filter empty and commented lines
            if not line_content or line_content[0] == '#':
                continue
            line = filter( bool, line_content.replace( '\t', ' ').split(' '))
            # Store ID as integers
            resources[ lineno ] = {
                    #first token on the host file is the ip
                    'ip' : line[0],
                    #remaining is the list of hostnames
                    'hostnames' : line[1:]
                    }
        return resources

    def generate_new_id( self, resource_dict):
        #In order to avoid concurrency issue we add a blank line
        # in the lines attribute so that another call
        # may not give the same line number

        #force load to be run
        self.resources
        #Add an empty line
        self.lines.append('')
        #return the position of that line
        return len( self.lines)

    def save( self, parent, resources):
        new_file_content = [ '\n' ] * len( self.lines)
        for lineno, original in enumerate( self.lines):
            stripped = original.strip()

            #Keep the comments in the file
            if stripped and stripped[0] == '#':
                new_file_content[lineno] =  original
                continue

            res_id = lineno + 1
            if stripped and res_id not in resources:
                #the resource existed and has been removed
                new_file_content[lineno] = '#;deleted: ' + original
                continue

            if res_id in resources:
                #the resource exists and may have been modified
                new_file_content[lineno] = ( '%s %s\n' % (
                    resources[ res_id ][ 'ip' ],
                    ' '.join(resources[ res_id ][ 'hostnames' ]),
                    ))

        handle = open( self.FILE_PATH , 'wb')
        handle.write( ''.join( new_file_content))

    def validate_resource_hostnames( self, hostnames):
        if ( not isinstance( hostnames, list) or
                not all([ isinstance(x, str) for x in hostnames ])):
            raise ValidationError, 'Hostnames have to be an array of strings'
        return hostnames

    def validate_resource_ip( self, ip):
        if not isinstance( ip, str):
            raise ValidationError, 'ip have to be a string'
        ip_components = ip.split('.')
        if len(ip_components) != 4:
            # 123.45.67 is not an ip
            raise ValidationError, 'Not an ip 1'
        try:
            ip_components = map(int,ip_components)
        except ValueError:
            #123.45.lol.99 is not an ip
            raise ValidationError, 'Not an ip 2'
        if not all([0 <= x <= 255 for x in ip_components]):
            #123.45.67.890 is not an ip
            raise ValidationError, 'Not an ip 3'
        #filter the useless 0 out of 123.045.012.001
        return '.'.join(map(str,ip_components))

    def validate_id( self, id_):
        try:
            return int( id_)
        except (ValueError, TypeError):
            raise ValidationError, 'id have to be integer values'

    def configure( self, conf):
        self.FILE_PATH = conf.get( 'file_path', self.FILE_PATH )
