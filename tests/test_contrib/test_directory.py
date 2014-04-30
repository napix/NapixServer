#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.contrib.directory import NapixDirectoryManager
from napixd.http.request import Request
from napixd.exceptions import NotFound


class TestDirectory(unittest.TestCase):
    def setUp(self):
        self.request = r = mock.Mock()
        self.ndm = NapixDirectoryManager(None, r)
        with mock.patch('napixd.contrib.directory.Store') as Store:
            self.ndm.configure({})
        self.store = Store.return_value

        store = {
            'dns.napix.io': {
                'last_seen': 15000,
            },
            '1.vm.napix.io': {
                'last_seen': 14500,
            },
            '2.vm.napix.io': {
                'last_seen': 10000,
            }
        }
        self.store.keys.side_effect = store.keys
        self.store.__getitem__.side_effect = store.__getitem__
        self.store.__delitem__.side_effect = store.__delitem__

    def test_list_resource(self):
        self.store.keys.side_effect = None
        self.store.keys.return_value = [
            'dns.napix.io',
            '1.vm.napix.io',
        ]

        with mock.patch('time.time') as time:
            time.return_value = 15000
            resp = self.ndm.list_resource()

        self.assertEqual(self.store.save.call_count, 0)
        self.assertEqual(resp, ['dns.napix.io', '1.vm.napix.io'])

    def test_list_resource_delete(self):

        with mock.patch('time.time') as time:
            time.return_value = 15000
            resp = self.ndm.list_resource()

        self.store.__delitem__.assert_called_once_with('2.vm.napix.io')
        self.store.save.assert_called_once_with()

        self.assertEqual(sorted(resp), ['1.vm.napix.io', 'dns.napix.io'])

    def test_get_resource_ok(self):
        with mock.patch('time.time') as time:
            time.return_value = 15000
            res = self.ndm.get_resource('dns.napix.io')

        self.assertEqual(res['status'], 'OK')

    def test_get_resource_waiting(self):
        with mock.patch('time.time') as time:
            time.return_value = 15000 + 600
            res = self.ndm.get_resource('dns.napix.io')

        self.assertEqual(res['status'], 'WAITING')

    def test_get_resource_lost(self):
        with mock.patch('time.time') as time:
            time.return_value = 15000 + 900
            res = self.ndm.get_resource('dns.napix.io')

        self.assertEqual(res['status'], 'LOST')

    def test_get_resource_forgotten(self):
        with mock.patch('time.time') as time:
            time.return_value = 15000 + 3300
            self.assertRaises(NotFound, self.ndm.get_resource, 'dns.napix.io')

        self.store.__delitem__.assert_called_once_with('dns.napix.io')
        self.store.save.assert_called_once_with()
