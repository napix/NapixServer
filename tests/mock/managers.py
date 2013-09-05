#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from napixd.managers.managed_classes import ManagedClass
from napixd.managers.resource_fields import ResourceFieldsDict
import mock

def get_managers():
    resource_fields = mock.MagicMock( spec=ResourceFieldsDict)
    resource_fields.__iter__.return_value = [ 'f1', 'f2']

    Managed = mock.Mock(
            name = 'managed',
            **{
                '_resource_fields' : resource_fields,
                'get_name.return_value' : 'my-mock',
                'get_all_actions.return_value' : [],
                'direct_plug.return_value' : None,
                }
            )
    Managed.return_value.__class__ = Managed
    managed_classes = [
            mock.Mock(
                spec=ManagedClass,
                manager_class=Managed,
                **{
                    'get_name.return_value' : 'my-middle-mock'
                    }
                )
            ]

    Manager = mock.Mock(
            name = 'manager',
            **{
                '_resource_fields' : resource_fields,
                'get_managed_classes.return_value' : managed_classes,
                'direct_plug.return_value' : False,
                'get_name.return_value' : 'this-mock',
                'get_all_actions.return_value' : [],
                'return_value.create_resource.return_value' : 'blue',
                'return_value.serialize.side_effect' : lambda x:x,
                }
            )
    Manager_direct = mock.Mock(
            name = 'manager_direct',
            **{
                '_resource_fields' : resource_fields,
                'get_managed_classes.return_value' : managed_classes,
                'direct_plug.return_value' : True,
                'get_name.return_value' : 'this-mock',
                'get_all_actions.return_value' : [],
                })
    return Managed, Manager, Manager_direct
Managed, Manager, Manager_direct = get_managers()
