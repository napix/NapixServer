#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
import os.path
import __builtin__
from cStringIO import StringIO

from napixd.conf import Conf

class TestConf(unittest2.TestCase):
    def setUp(self):
        self.conf = Conf( {
            'a' : {
                'a1' : {
                    'a1a' : 'foo',
                    'a1b' : 'bar'
                    },
                'a2' : {
                    'x' : 1,
                    'y' : 2
                    }
                },
            'b' : {
                'mpm' : 'prefork'
                },
            'c' : 'blo'
            })
    def test_get(self):
        self.assertEqual( self.conf.get('c'), 'blo')

    def test_get_inexisting( self):
        self.assertEqual( self.conf.get('d'), {})

    def test_get_dotted(self):
        self.assertEqual( self.conf.get('a.a1.a1b'), 'bar')
        self.assertEqual( self.conf.get('b.mpm'), 'prefork')

    def test_inherit(self):
        self.assertEqual( self.conf.get('a').get('a1').get('a1a'), 'foo')
        self.assertEqual( self.conf.get('a').get('a2'), { 'x' : 1 ,'y' : 2 })

class TestConfLoader( unittest2.TestCase ):
    good_json1 = '{"json" : { "v" : 1 } }'
    good_json2 = '{"json" : { "v" : 2 } }'
    bad_json = '{"badjson'
    conf_file = os.path.realpath( os.path.join( os.path.dirname( __file__), '..', 'conf', 'settings.json'))

    @classmethod
    def setUpClass( cls ):
        cls.old_open = Conf.open
    @classmethod
    def tearDownClass( cls):
        Conf.open = cls.old_open

    def setUp(self):
        Conf.open = self._open
        self.calls = []

    def _open(self, filename, mode='r'):
        self.calls.append( filename )
        if not filename in self.filesystem:
            raise IOError, 'No such file or directory'
        else:
            return StringIO( self.filesystem[filename])

    def test_bad_json(self):
        self.filesystem = {
                '/etc/napixd/settings.json': self.bad_json,
                 self.conf_file : self.good_json2
                }
        conf = Conf.make_default()
        self.assertTrue( 'v' in conf['json'])
        self.assertEqual( conf.get('json.v'), 2)

    def test_load_system(self):
        self.filesystem = {
                '/etc/napixd/settings.json': self.good_json1,
                }
        conf = Conf.make_default()
        self.assertTrue( 'v' in conf['json'])
        self.assertEqual( len( self.calls), 3)

    def test_load_multiple(self):
        self.filesystem = {
                '/etc/napixd/settings.json': self.good_json1,
                 self.conf_file : self.good_json2
                }
        conf = Conf.make_default()
        self.assertTrue( 'v' in conf['json'])
        self.assertEqual( conf.get('json.v'), 1)

    def test_load_sources(self):
        self.filesystem = {
                self.conf_file : self.good_json2
                }
        conf = Conf.make_default()
        self.assertTrue( 'v' in conf['json'])

    def test_get_default(self):
        self.filesystem = {
                '/etc/napixd/settings.json': self.good_json1,
                 self.conf_file : self.good_json2
                }
        Conf.make_default()
        self.assertEqual( Conf.get_default(), { 'json' : { 'v' : 1} } )
        self.assertEqual( Conf.get_default('json'), { 'v' : 1} )
        self.assertEqual( Conf.get_default('json.v'), 1)

    def test_no_file(self):
        self.filesystem = { }
        conf = Conf.make_default()
        self.assertEqual( conf.keys(), [])


    def test_force(self):
        self.filesystem = {
                self.conf_file : self.good_json1
                }
        conf = Conf.make_default()
        self.assertEqual( Conf.get_default('json.v'), 1)
        with conf.force( 'json.v', 3):
            self.assertEqual( Conf.get_default('json.v'), 3)

if __name__ == '__main__':
    unittest2.main()
