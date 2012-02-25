#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napix.manager import Manager
from napix.executor import run_comman_or_fail, executor
from napix.exceptions import NotFound, ValidationError
import subprocess

class LVMManager( Manager ):
    """
    LVM logical volumes manager
    """
    resource_fields = {
            'name' : {
                'description' : '',
                'example' : 'lv_home'
                },
            'group' : {
                'description' : '',
                'example' : 'lv_home'
                },
            'size' : {
                'description' : 'Total size of the logical volume in Mo',
                'example' : '20000'
                }
            }

    def list_resource( self):
        #run the command that spit the UUID line by line
        process = executor.create_job(
                ['sudo','lvm','lvs','--nosuffix', '--noheading',
                    '--separator',';','-o','lv_uuid'], discard_output= False)
        #if the command fail it raises an exception
        # that will be catched by napix and will return a 500 error
        if process.wait() != 0:
            raise subprocess.CalledProcessException(
                'The command exited with a non 0 return code'+
                process.stderr.read())

        return filter( bool,
                map( str.strip, process.stdout.read().split('\n')))

    def get_resource( self, uuid):
        process = executor.create_job(
                ['sudo','lvm','lvs','--nosuffix', '--noheading',
                    '--separator',';','-o',
                    'lv_uuid,lv_size,lv_name,vg_name' ], discard_output= False)
        if process.wait() != 0:
            raise subprocess.CalledProcessException(
                'The command exited with a non 0 return code'+
                process.stderr.read())
        for lv in map( str.strip, process.stdout.read().split('\n')):
            lv_uuid, lv_size, lv_name, vg_name = lv.split(';')
            if uuid == lv_uuid:
                return {
                        'name' : lv_name,
                        'size' : float( lv_size.replace(',','.')),
                        'group' : vg_name
                        }
        raise NotFound, uuid

    def validate_resource( self, data_dict):
        super( LVMManager, self).validate_resource( data_dict)
    def validate_resource_name( self, name):
        if '/' in name:
            raise ValidationError, 'Name cannot contain /'
        return name
    def validate_resource_group( self, group):
        ['sudo','lvm','vgs','--noheading','-o','vg_name'@
        if '/' in group:
            raise ValidationError, 'Group cannot contain /'
        return group
    def validate_resource_size( self, size):
        try:
            size = float( size)
            if size > 0:
                return size
        except (ValueError, TypeError):
            pass
        raise ValidationError, 'size must be a positive number'

