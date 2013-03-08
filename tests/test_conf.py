#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest2
import napixd
from cStringIO import StringIO
import mock

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

    def test_not_truthy(self):
        self.assertFalse( bool( self.conf.get('d')))
    def test_truthy(self):
        self.assertTrue( bool( self.conf.get('a')))
        self.assertTrue( bool( self.conf.get('c')))

class TestConfLoader( unittest2.TestCase ):
    good_json1 = '{"json" : { "v" : 1 } }'
    good_json2 = '{"json" : { "v" : 2 } }'
    bad_json = '{"badjson'
    conf_file = napixd.get_file( 'conf/settings.json', create=False)

    def setUp(self):
        self.patch_open = mock.patch('napixd.conf.open', side_effect = self._open)

    def _open(self, filename, mode='r'):
        if not filename in self.filesystem:
            raise IOError, 'No such file or directory'
        else:
            return StringIO( self.filesystem[filename])

    def test_bad_json(self):
        self.filesystem = {
                '/etc/napixd/settings.json': self.bad_json,
                 self.conf_file : self.good_json2
                }
        with self.patch_open:
            conf = Conf.make_default()
        self.assertTrue( 'v' in conf['json'])
        self.assertEqual( conf.get('json.v'), 2)

    def test_load_system(self):
        self.filesystem = {
                '/etc/napixd/settings.json': self.good_json1,
                }

        with self.patch_open as patched_open:
            conf = Conf.make_default()
        self.assertTrue( 'v' in conf['json'])
        self.assertEqual( len( patched_open.mock_calls), 3)

    def test_load_multiple(self):
        self.filesystem = {
                '/etc/napixd/settings.json': self.good_json1,
                 self.conf_file : self.good_json2
                }
        with self.patch_open:
            conf = Conf.make_default()
        self.assertTrue( 'v' in conf['json'])
        self.assertEqual( conf.get('json.v'), 1)

    def test_load_sources(self):
        self.filesystem = {
                self.conf_file : self.good_json2
                }
        with self.patch_open:
            conf = Conf.make_default()
        self.assertTrue( 'v' in conf['json'])

    def test_get_default(self):
        self.filesystem = {
                '/etc/napixd/settings.json': self.good_json1,
                 self.conf_file : self.good_json2
                }
        with self.patch_open:
            Conf.make_default()
        self.assertEqual( Conf.get_default(), { 'json' : { 'v' : 1} } )
        self.assertEqual( Conf.get_default('json'), { 'v' : 1} )
        self.assertEqual( Conf.get_default('json.v'), 1)

    def test_no_file(self):
        self.filesystem = { }
        with self.patch_open:
            conf = Conf.make_default()
        self.assertEqual( conf.keys(), [])


    def test_force(self):
        self.filesystem = {
                self.conf_file : self.good_json1
                }
        with self.patch_open:
            conf = Conf.make_default()
        with conf.force( 'json.v', 3):
            self.assertEqual( Conf.get_default('json.v'), 3)
        self.assertEqual( Conf.get_default('json.v'), 1)

    def test_force_dict(self):
        self.filesystem = {
                self.conf_file : self.good_json1
                }
        with self.patch_open:
            conf = Conf.make_default()
        with conf.force( 'json', { 'v' : 12, 'y': 14 }):
            self.assertEqual( Conf.get_default('json.v'), 12)
            self.assertEqual( Conf.get_default('json.y'), 14)
        self.assertEqual( Conf.get_default('json.v'), 1)
        self.assertFalse( bool( Conf.get_default('json.y')))

if __name__ == '__main__':
    unittest2.main()
