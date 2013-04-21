#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from napixd.managers.managed_classes import ManagedClass
import mock

def get_managers():
    resource_fields = {
                    'lol' : {
                        },
                    'blabla' : {
                        }
                    }
    managed = mock.Mock(
            name = 'managed',
            **{
                'managed_class'  : None,
                'get_name.return_value' : 'my-mock',
                'get_all_actions.return_value' : [],
                'resource_fields' : resource_fields,
                'return_value.resource_fields' : resource_fields,
                }
            )
    managed_classes = [
            mock.Mock(
                spec=ManagedClass,
                manager_class=managed,
                **{
                    'get_name.return_value' : 'my-middle-mock'
                    }
                )
            ]

    manager = mock.Mock(
            name = 'manager',
            **{
                'managed_class'  : [ managed ],
                'get_managed_classes.return_value' : managed_classes,
                'direct_plug.return_value' : False,
                'get_name.return_value' : 'this-mock',
                'get_all_actions.return_value' : [],
                'resource_fields' : resource_fields,
                'return_value.resource_fields' : resource_fields,
                'return_value.create_resource.return_value' : 'blue',
                'return_value.serialize.side_effect' : lambda x:x,
                }
            )
    manager_direct = mock.Mock(
            name = 'manager_direct',
            **{
                'managed_class'  : managed,
                'get_managed_classes.return_value' : managed_classes,
                'direct_plug.return_value' : True,
                'get_name.return_value' : 'this-mock',
                'get_all_actions.return_value' : [],
                'resource_fields' : resource_fields,
                'return_value.resource_fields' : resource_fields,
                })
    return managed, manager, manager_direct
managed, manager, manager_direct = get_managers()
