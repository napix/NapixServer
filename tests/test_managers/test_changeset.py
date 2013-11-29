#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from napixd.managers.changeset import DiffDict


class TestDiffDict(unittest.TestCase):

    def setUp(self):
        self.cs = DiffDict({
            'changed': 1,
            'deleted': 2,
            'untouched': 3,
        }, {
            'changed': 4,
            'new': 2,
            'untouched': 3,
        })

    def test_getitem(self):
        self.assertEqual(self.cs['changed'], 4)
        self.assertEqual(self.cs['new'], 2)

    def test_iter(self):
        self.assertEqual(dict(self.cs), {
            'changed': 4,
            'new': 2,
            'untouched': 3,
        })

    def test_new_fields(self):
        self.assertEqual(self.cs.added, set(['new']))

    def test_deleted_fields(self):
        self.assertEqual(self.cs.deleted, set(['deleted']))

    def test_changed_fields(self):
        self.assertEqual(self.cs.changed, set(['changed']))

    def test_add_new_key(self):
        self.cs['added_after'] = 1
        self.assertEqual(self.cs.added, set(['new', 'added_after']))

    def test_reset_changed(self):
        self.cs['changed'] = 5
        self.assertEqual(self.cs.added, set(['new']))
        self.assertEqual(self.cs.changed, set(['changed']))

    def test_set_changed_original(self):
        self.cs['changed'] = 1
        self.assertEqual(self.cs.changed, set())

        self.assertEqual(self.cs['changed'], 1)

    def test_change_untouched(self):
        self.cs['untouched'] = 5
        self.assertEqual(self.cs.added, set(['new']))
        self.assertEqual(self.cs.changed, set(['changed', 'untouched']))

        self.assertEqual(self.cs['untouched'], 5)

    def test_change_deleted(self):
        self.cs['deleted'] = 5
        self.assertEqual(self.cs.deleted, set())
        self.assertEqual(self.cs.added, set(['new']))
        self.assertEqual(self.cs.changed, set(['changed', 'deleted']))

        self.assertEqual(self.cs['deleted'], 5)


    def test_delete_untouched(self):
        del self.cs['untouched']
        self.assertEqual(self.cs.deleted, set(['deleted', 'untouched']))
        self.assertEqual(self.cs.added, set(['new']))
        self.assertEqual(self.cs.changed, set(['changed']))

        self.assertFalse('untouched' in self.cs)

    def test_delete_changed(self):
        del self.cs['changed']
        self.assertEqual(self.cs.deleted, set(['deleted', 'changed']))
        self.assertEqual(self.cs.added, set(['new']))
        self.assertEqual(self.cs.changed, set())
