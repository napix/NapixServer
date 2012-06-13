from napixd.managers.default import DictManager

import os

class BasicPasswordFileManager(DictManager):
    """
    Napix server to edit a password file in the user:password format
    """
    FILE_PATH  = '/tmp/test'
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

    def load(self, parent):
        if not os.path.exists(self.FILE_PATH):
            return {}
        # Read the file
        content =  file(self.FILE_PATH).read()
        # split the file in line
        userpass = content.split("\n")
        # split each line in a tuple and build the corresponding resource dict list
        userpass = [ i.split(":", 1) for i in userpass ]
        resources = [ { "username": user, "password": password }
                      for user, password in userpass ]
        # Then we transform the list in a dict, indexing ressource with and uniq id
        # We'll use username as the id as it's supposed to be unique in our password files.
        return dict([ (resource["username"], resource)
                      for resource in resources ])
    
    def generate_new_id( self, resource_dict):
        # in this case, getting a id for new object is simple, it's the username
        return resource_dict["username"]

    def save(self, parent, resources):
        # Generate the new file
        content = []
        for index, resource in resources.items():
            content.append("%(username)s:%(password)s"%resource)
        content = "\n".join(content) + "\n"
        file(self.FILE_PATH, "w").write(content)
        
