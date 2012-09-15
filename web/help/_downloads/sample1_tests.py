#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os

from sample1 import HostManager
from napixd.exceptions import ValidationError

class TestHostFile( unittest.TestCase):
    SAMPLE_FILE = os.path.join(
                '/dev/shm',
                'napix_sample_hosts')
    SAMPLE_CONTENT = """
127.0.0.1 localhost

#A.com and its alias
127.0.0.2 a.com www.a.com
"""
    def setUp( self):
        open( self.SAMPLE_FILE, 'w').write( self.SAMPLE_CONTENT)
        self.manager = HostManager( None )
        HostManager.FILE_PATH = self.SAMPLE_FILE
    def tearDown( self):
        os.unlink( self.SAMPLE_FILE)

    def test_load( self):
        self.assertDictEqual( self.manager.resources,
                {
                    2 : {
                        'ip' : '127.0.0.1',
                        'hostnames' : [ 'localhost' ]
                        },
                    5 : {
                        'ip' : '127.0.0.2',
                        'hostnames' : [ 'a.com', 'www.a.com' ]
                        }
                    })
    def test_get_new_id( self):
        self.assertEqual( self.manager.generate_new_id({}), 6)

    def test_noop_save( self):
        self.manager.save( None, self.manager.resources)
        self.assertEqual(
                open( self.SAMPLE_FILE).read(),
                self.SAMPLE_CONTENT)
    def test_delete_save( self):
        self.manager.delete_resource(2)
        self.manager.save( None, self.manager.resources)
        self.assertEqual(
                open( self.SAMPLE_FILE).read(), """
#;deleted: 127.0.0.1 localhost

#A.com and its alias
127.0.0.2 a.com www.a.com
"""
                )
    def test_modify_save( self):
        self.manager.modify_resource(
                2,
                { 'ip' : '127.0.0.1',
                    'hostnames' : ['localhost', 'localhost.com']
                })
        self.manager.save( None, self.manager.resources)
        self.assertEqual(
                open( self.SAMPLE_FILE).read(), """
127.0.0.1 localhost localhost.com

#A.com and its alias
127.0.0.2 a.com www.a.com
"""
                )
    def test_create_resource( self):
        self.manager.create_resource(
                { 'ip' : '8.8.8.8',
                    'hostnames' : ['google-public-dns-a.google.com']
                    })
        self.manager.save( None, self.manager.resources)
        self.assertEqual(
                open( self.SAMPLE_FILE).read(), """
127.0.0.1 localhost

#A.com and its alias
127.0.0.2 a.com www.a.com
8.8.8.8 google-public-dns-a.google.com
"""
                )

    def test_validate_resource( self):
        self.assertListEqual(
                self.manager.validate_resource_hostnames( ['host1']),
                ['host1'])
        self.assertListEqual(
                self.manager.validate_resource_hostnames( ['host1', 'host2']),
                ['host1', 'host2'])
        self.assertRaises( ValidationError,
                self.manager.validate_resource_hostnames,
                [ 'host1', 0 ])
        self.assertRaises( ValidationError,
                self.manager.validate_resource_hostnames,
                'host1' )

    def test_validate_ip( self):
        self.assertEqual(
                self.manager.validate_resource_ip( '127.0.0.1' ),
                '127.0.0.1')
        self.assertEqual(
                self.manager.validate_resource_ip( '1.10.0.01' ),
                '1.10.0.1')
        self.assertRaises(
                ValidationError,
                self.manager.validate_resource_ip,
                '1.2.3')
        self.assertRaises(
                ValidationError,
                self.manager.validate_resource_ip,
                '1.2.3.10000')
        self.assertRaises(
                ValidationError,
                self.manager.validate_resource_ip,
                '1.2.3.lol')

    def test_validate_id( self):
        self.assertEqual( self.manager.validate_id('1'), 1)
        self.assertEqual( self.manager.validate_id('0'), 0)
        self.assertRaises(
                ValidationError,
                self.manager.validate_id, 'lpm')
        self.assertRaises(
                ValidationError,
                self.manager.validate_id, '')


if __name__ == '__main__':
    unittest.main()
