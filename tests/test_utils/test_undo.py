#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import mock

from napixd.utils.undo import UndoManager


class TestUndoManager(unittest.TestCase):
    def setUp(self):
        self.um = UndoManager()
        self.undo_cb = mock.Mock()

    def test_as_decorator(self):
        @self.um.register
        def rollback():
            self.undo_cb.m1()

        self.um.undo()
        self.undo_cb.m1.assert_called_once_with()

    def test_undo(self):
        self.undo_cb.m2.side_effect = ValueError
        orig = Exception()
        try:
            with self.um:
                self.um.register(self.undo_cb.m1)
                self.um.register(self.undo_cb.m2)
                self.um.register(self.undo_cb.m3)
                raise orig
        except Exception as e:
            self.assertTrue(e is orig)
        else:
            self.fail()

        self.assertEqual(self.undo_cb.mock_calls, [
            mock.call.m3(),
            mock.call.m2(),
            mock.call.m1(),
        ])

    def test_not_undo(self):
        with self.um:
            self.um.register(self.undo_cb.m1)
            self.um.register(self.undo_cb.m2)
            self.um.register(self.undo_cb.m3)

        self.assertEqual(self.undo_cb.mock_calls, [])

    def test_undo_nothing(self):
        orig = Exception()
        try:
            with self.um:
                raise orig
        except Exception as e:
            self.assertTrue(e is orig)
