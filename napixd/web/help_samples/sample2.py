#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napix.manager import Manager
from napix.executor import run_comman_or_fail, executor
from napix.exceptions import NotFound, ValidationError, Duplicate
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

    def _lv_list( self):
        process = executor.create_job(
                ['sudo','lvm','lvs','--nosuffix', '--noheading',
                    '--separator',';','-o',
                    'lv_uuid,lv_size,lv_name,vg_name' ], discard_output= False)
        if process.wait() != 0:
            raise subprocess.CalledProcessException(
                'The command exited with a non 0 return code'+
                process.stderr.read())
        for lv in map( str.strip, process.stdout.read().split('\n')):
            if lv:
                yield lv.split(';')

    def _vg_list( self):
        process = executor.create_job(['sudo','lvm','vgs','--noheading','-o','vg_name'])
        process.wait()
        return map( str.strip, process.stdout.split('\n'))

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
        for lv_uuid, lv_size, lv_name, vg_name in self._lv_list() :
            if uuid == lv_uuid:
                return {
                        'name' : lv_name,
                        'size' : float( lv_size.replace(',','.')),
                        'group' : vg_name
                        }
        raise NotFound, uuid

    def validate_resource_name( self, name):
        if '/' in name:
            raise ValidationError, 'Name cannot contain /'
        return name

    def validate_resource_group( self, group):
        vg_list = self._vg_list()
        if group not in vg_list:
            raise ValidationError, 'Group must be one of %s' % ','.join(vg_list)
        return group

    def validate_resource_size( self, size):
        try:
            size = float( size)
            if size > 0:
                return size
        except (ValueError, TypeError):
            pass
        raise ValidationError, 'size must be a positive number'

    def create_resource( self, data_dict):
        process = executor.create_job( ['sudo', 'lvcreate',
            '--size', '%dm' % data_dict['size'],
            '--name', data_dict['name'],
            data_dict['group']
            ])
        code= process.wait()
        if code != 0:
            raise Exception, 'command finished with code %d' % code

        for lv_uuid, lv_size, lv_name, vg_name in self._lv_list() :
            if lv_name == data_dict['name'] and vg_name == data_dict['group']:
                return lv_uuid

    def delete_resource( self, uuid):
        lv = self.get_resource( uuid)
        process = executor.create_job( [ 'sudo', 'lvremove',
            '%s/%s'% ( lv['group'], lv['name']) ] )

        code= process.wait()
        if code != 0:
            raise Exception, 'command finished with code %d' % code
