#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from napixd.managers.changeset import ChangeSet


class TestChangeSet(unittest.TestCase):
    def setUp(self):
        self.cs = ChangeSet({
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
        self.assertEqual(self.cs.new_fields, set(['new']))

    def test_deleted_fields(self):
        self.assertEqual(self.cs.deleted_fields, set(['deleted']))

    def test_changed_fields(self):
        self.assertEqual(self.cs.changes, set(['changed']))
