#!/usr/bin/env python

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
        try:
            handle = open( self.FILE_PATH, 'rb')
        except IOError:
            #There is no file, consider it as empty
            return {}
        self.lines = handle.readlines()
        handle.close()
        resources = {}
        for lineno, line_content in enumerate( map( str.strip, self.lines ), 1):
            #filter empty and commented lines
            if not line_content or line_content[0] == '#':
                continue
            line = filter( bool, line_content.replace( '\t', ' ').split(' '))
            # Store ID as strings
            resources[ str(lineno) ] = {
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
        return str(len( self.lines))

    def save( self, parent, resources):
        new_file_content = [ '\n' ] * len( self.lines)
        for lineno, original in enumerate( self.lines):
            lineno = int( lineno )
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
