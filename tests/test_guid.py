#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import
import unittest
import mock
import uuid

from napixd.guid import NapixID

class TestGUID(unittest.TestCase):
    def setUp(self):
        self.uid = NapixID()

    def test_load_exists_not(self):
        with mock.patch( 'napixd.guid.open', side_effect=IOError('OH SNAP')):
            uid = self.uid.load()
        self.assertEqual( uid, None)

    def test_load(self):
        with mock.patch( 'napixd.guid.open', **{ 'return_value.read.return_value' : '2550ba7b-aec4-4a67-8047-2ce1ec8ca8ae\n' }):
            uid = self.uid.load()
        self.assertEqual( uuid.UUID( '2550ba7b-aec4-4a67-8047-2ce1ec8ca8ae'), uid)

    def test_load_garbage(self):
        with mock.patch( 'napixd.guid.open', **{ 'return_value.read.return_value' : 'garbage_garbage' }):
            self.assertRaises( ValueError, self.uid.load)


    def test_lazy_load(self):
        with mock.patch( 'napixd.guid.open', **{ 'spec':open, 'return_value.read.return_value' : '2550ba7b-aec4-4a67-8047-2ce1ec8ca8ae\n' }) as opn:
            uid1 = self.uid.uuid
            uid2 = self.uid.uuid
        self.assertEqual( len( opn.call_args_list), 1)
        self.assertEqual( uuid.UUID( '2550ba7b-aec4-4a67-8047-2ce1ec8ca8ae'), uid1)
        self.assertEqual( uid2, uid1)

    def test_generation(self):
        opn = mock.MagicMock()
        with mock.patch( 'napixd.guid.open', side_effect=[ IOError('OH SNAP'), opn ]):
            with mock.patch( 'napixd.guid.uuid.uuid4', return_value=uuid.UUID( '2550ba7b-aec4-4a67-8047-2ce1ec8ca8ae')):
                uid1 = self.uid.uuid
        self.assertEqual( opn.write.call_args_list, [ mock.call( '2550ba7b-aec4-4a67-8047-2ce1ec8ca8ae') ])
        self.assertEqual( uuid.UUID( '2550ba7b-aec4-4a67-8047-2ce1ec8ca8ae'), uid1)
