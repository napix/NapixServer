#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
===============
Managers Mixins
===============


This modules defines Mixin classes for frequent scenarios.
"""


class AttrResourceMixin(object):

    """
    This mixin overrides the serialize method to returns a new dict
    of the declared fields and the corresponding attributes of the resource.

    .. code-block:: python

        class MyManager( AttrResourceMixin, Manager):
            resource_fields = {
                'fieldA' : {},
                'fieldB' : {}
            }
            def get_resource( self, id_):
                return get_object_from_existing_function( id_ )

        manager = MyManager({})
        resource = m.get_resource( 1 )
        <MyObject id: 1 >
        #Custom object with its own business for the the action, the sub-managers, etc.

        manager.serialize( resource )
        {
            'fieldA' : 'valueA',
            'fieldB' : 'valueB'
        }
        #Dictionary serialized for JSON transport


    """

    def serialize(self, resource):
        return dict((k, getattr(resource, k))
                    for k in self.__class__._resource_fields.keys())
