#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from napixd.managers import Manager
from napixd.managers.default import DictManager
from napixd.exceptions import ValidationError, NotFound

class HTAccessManager( Manager):
    """ Manages the protection of the directories of the users """

    VHOSTPATH = '/var/http/virtualhosts'
    PASSPATH = '/var/http/passwords'

    managed_class = [ 'PasswordsManager' ]

    resource_fields = {
            'enabled' : {
                'description': '',
                'example': True
                },
            'authname' : {
                'description': '',
                'example': 'Please enter your login and password'
                }
            }

    @classmethod
    def get_name(cls):
        return 'htaccess'

    def validate_id( self, id_):
        if '/' in id_:
            raise ValidationError, 'ID do not contain a /'
        return id_

    def validate_resource_authname( self, message):
        if not isinstance( message, basestring):
            raise ValidationError, 'message should be a string'
        return message.replace('\n', ' ')

    def validate_resource_enabled(self, enabled):
        return bool( enabled)

    def get_resource( self, id_):
        #get the file path
        path = os.path.join( self.VHOSTPATH, id_, '.htaccess')
        #initialize an empty resource
        resource = {
                'enabled' : False,
                'authname' : '',
                'authuserfile' : os.path.join( self.PASSPATH, id_)
                }
        try:
            #try to open
            handle = open( path, 'r')
        except IOError:
            if os.path.isdir( os.path.join( self.VHOSTPATH, id_)):
                #in case of failure, return the empty resource if the vhost exists 
                return resource
            #else indicate that it is not found.
            raise NotFound, id_

        #parse the file.
        lines = handle.readlines()
        for line in map( str.strip, lines):
            if line.startswith( 'Require'):
                resource['enabled'] = True
            if line.startswith( 'AuthName'):
                x, resource['authname'] = line.split(' ',1)
        return resource

    def modify_resource( self, id_, resource_dict):
        userfile = os.path.join( self.PASSPATH, id_)
        path = os.path.join( self.VHOSTPATH, id_, '.htaccess')

        handle = open( path, 'wb')
        content = '''
AuthUserFile {userfile}
AuthType Basic
AuthName {authname}
{require}
'''

        handle.write( content.format(
            require = 'Require valid-user' if resource_dict['enabled'] else '',
            userfile =  userfile,
            **resource_dict))
        handle.close()

    def list_resource( self ):
        return list( self._list_resource())

    def _list_resource(self):
        for file_ in os.listdir(self.VHOSTPATH):
            if file_[0] == '.':
                continue
            yield file_


class PasswordsManager(DictManager):
    """
    Napix server to edit a password file in the user:password format
    """

    FILE_PATH  = '/tmp/test'
    PASS_MIN_SIZE  = 6

    resource_fields = {
        'username':{
            'description':'Username',
            'example': 'john'
            },
        'password':{
            'description':'Password associated with the username',
            'example':'toto42'
            }
    }

    @classmethod
    def get_name(cls):
        return 'passwords'

    def load(self, parent):
        path = parent['authuserfile']
        if not os.path.exists(path):
            return {}
        # Read the file
        content =  open(path, 'r' )
        # split the file in line
        resources = {}
        for line in content.readlines():
            username, password = line.strip().split(':',1)
            resources[username] =  {
                    'username' : username,
                    'password' : password
                    }
        return resources

    def generate_new_id( self, resource_dict):
        # in this case, getting a id for new object is simple, it's the username
        return resource_dict["username"]

    def save(self, parent, resources):
        # Generate the new file
        content = []
        for resource in resources.values():
            content.append("%(username)s:%(password)s"%resource)
        content = "\n".join(content) + "\n"
        open(parent['authuserfile'], "w").write(content)

    def validate_resource_username( self, username):
        #avoid injections
        if '\n' in username or ':' in username:
            raise ValidationError, r'Username cannot contain `\n` nor `:`'
        #always return the valid value
        return username

    def validate_resource_password( self, password):
        #avoid injections
        if '\n' in password:
            raise ValidationError, r'Password cannot contain `\n`'
        #check the minimum size of the password
        if len( password) < self.PASS_MIN_SIZE:
            raise ValidationError, r'Password must be at least %s characters long' % self.PASS_MIN_SIZE
        #always return the valid value
        return password

    def validate_resource( self, resource_dict):
        if resource_dict['username'] in resource_dict['password']:
            raise ValidationError, 'Password must not contain the username'
        return resource_dict
