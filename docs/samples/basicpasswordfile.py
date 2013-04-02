#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from napixd.managers.default import DictManager
from napixd.exceptions import ValidationError




class BasicPasswordFileManager(DictManager):
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
        if not os.path.exists(self.FILE_PATH):
            return {}
        # Open the file, read it
        content =  file(self.FILE_PATH)
        # then populate a dict we'll return as our internal dict.
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
        file(self.FILE_PATH, "w").write(content)

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
        #Always return the valid resource
        return resource_dict
