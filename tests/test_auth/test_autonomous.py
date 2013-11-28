#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
import mock

from napixd.auth.autonomous import AutonomousAuthProvider
from napixd.http.request import Request
from napixd.conf import Conf


class TestAutonomous(unittest.TestCase):
    def setUp(self):
        self.ap = AutonomousAuthProvider(u'master_local', u'password')
        self.request = mock.Mock(spec=Request)
        self.content = {
            'login': 'master_local',
            'signature': 'bd4dfeebe49e0ce2a4edeaf9f32fb0ec80b638993a6ab695987545ca2ebce7df',
            'msg': 'master_local',
        }

    def call(self):
        return self.ap(self.request, self.content)

    def test_from_settings(self):
        ap = AutonomousAuthProvider.from_settings(Conf({
            'login': u'user',
            'password': u'that',
        }))
        self.assertEqual(ap.login, 'user')
        self.assertEqual(ap.password, 'that')

    def test_not_login(self):
        self.content['login'] = 'normal_login'
        self.assertTrue(self.call() is None)

    def test_login(self):
        self.assertTrue(self.call() is True)

    def test_login_bad(self):
        self.content['signature'] = 'blalblalbla'
        self.assertTrue(self.call() is False)
