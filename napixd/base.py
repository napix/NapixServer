#!/usr/bin/env python
# -*- coding: utf-8 -*-


from exceptions import ValidationError, NotFound

"""
Manager :
 - manage un ensemble de ressource
 - peut définir les methode delete/create/etcetc afin de delete/creer/etcetc des sous ressources

Ressource :
 - Est une ressource n'importe quelle classe qui émule un dict (representant la ressource elle même)


Les managers, comme les ressources, peuvent supporter des actions.

"""

                                                                                                    


class ManagerInterface(object, dict):
    """
    Define everything need to handle API call to manage ressource.

    Ressource must be a dict, or emulate it. Ressource should avoid to nest complex
    type (eg, dict containing a dict) if possible.

    
    """
    managed_class = None #: Class of the resource being managed
    resource_fields = {} #: Dictionnary of representative key in resource dict, associated with their doc.
    

    def default_resource(self):
        """
        Return a default dict to be used as template to create a new resource.

        Defaut value will be set to description string associated with each keyword.

        Get called with GET /something/[...]/mymanager/_napix_new
        """
        newdict = {}
        for key, description in self.resource_fields:
                newdict[key] = description.strip()
        return newdict
        

    def validate_resource(self, resource_dict):
        """
        Validate a resource_dict (which can be directly a dict or an object emulating a dict) by
        checking that every mandatory field specified in self.resource_fields is defined.

        If the current object implement self.validate_resource_<key> method, it'll be called with
        the value of resource_dict[<key>] as parameters, and shoud raise a ValidationError if it
        failed. If the method return something other than None, then the value with be remplaced
        with it result.

        Return a new resource_dict (which is always a dict).
        """
        # Create a new dict to populate with validated data
        newdict = {}
        for key, description in self.resource_fields:
            if "optionnal" not in description.lower() and key not in resource_dict:
                raise ValidationError("Field %s is missing in the supplyed resource"%key)
            validator = getattr(self, "validate_resource_%s"%key, None)
            if validator:
                tmp = validator(resource_dict[key])
                newvalue = tmp if (tmp != None) else resource_dict[key]
            else:
                newvalue = resource_dict[key]
            newdict[key] = newvalue
        return newdict


    def delete_resource(self,resource_id):
        """
        Delete a managed ressource.

        Eg :
        DEL /something/[...]/mymanager/42
        will be translated to :
        mymanager.delete_resource('42')

        """
        raise NotImplementedError

    def create_resource(self, resource_id, resource_dict):
        """
        Create a new managed ressource.

        resource_id parameters is either the id given in the URL, if present, or the result of
        self.new_resource_id(self, resource_dict)

        resource_dict is a dict populated with PUT/POSTED json resource_dict.

        Eg:
        POST /something/[...]/mymanager/ with resource_dict { 'toto': 1 }
        will be translated to :
        mymanager.create_resource(mymanager.new_resource_id({'toto': 1 }),
                                  { 'toto': 1})

        PUT /something/[...]/mymanager/42 with resource_dict { 'toto': 4242 }
        will be translated to :
        if mymanager.resource_exist('42'):
            mymanager.modify_resource('42', { 'toto': 4242 })
        else:
            mymanager.create_resource('42', {'toto': 4242 })

        """
        raise NotImplementedError

    def new_resource_id(self, resource_dict):
        """
        Return a new unique and suitable resource_id to be used to reference the resource
        represented by resource_dict.

        You could extract some revelant data from resource_dict and compute
        an unique id with them.

        By default, it retun resource_dict['_id'] and raise NotImplementedError if this key
        is undefined
        """
        try:
            return resource_dict["_id"]
        except:
            raise NotImplementedError    

    def list_resource_id(self):
        """
        Return the ids list of all managed resource. The result can be of 2 form : either a direct list
        of string, representing each id, or a list of dict, defining at least '_id' and '_desc' as key.

        Eg: GET /something/[...]/mymanager/
        will be translated to
        mymanager.list_resource_id()

        After processing, the nAPIx daemon will always convert the list in a list of dict, and add
        the _uri key with appropriate value (based on baseurl + _id).
        """
        raise NotImplementedError        


    def get_resource(self,resource_id):
        """
        Get the ressource object corresponding to resource_id.

        This object must be a dict or emulate it, as the nAPIxd will convert this dict
        to a json object to build his response.

        Eg: GET /somehting/[...]/mymanager/42
        call
        mymanager.get_resource(self, 42)

        """
        raise NotImplementedError


    def modify_resource(self,resource_id,resource_dict):
        """
        Modify the ressource designed by resource_id by updating it with resource_dict
        defined values.

        If modify_resource is not defined, it's emulated by calling delete/create sequentially.

        Eg: PUT /something/[...]/mymanager/42
        will be translated to :
        if mymanager.resource_exist('42'):
            mymanager.modify_resource('42', { 'toto': 4242 })
        else:
            mymanager.create_resource('42', {'toto': 4242 })

        """
        self.delete_resource(resource_id)
        return self.create_resource(resource_id, resource_dict)




    
