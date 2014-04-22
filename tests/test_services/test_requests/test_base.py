#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

from napixd.utils.lock import Lock

from napixd.services.collection import CollectionService
from napixd.services.contexts import CollectionContext

from napixd.services.requests.base import ServiceRequest


class MyServiceRequest(ServiceRequest):
    def call(self):
        return None

    def serialize(self, value):
        return None

    def get_callback(self):
        return mock.Mock()


class TestServiceRequest(unittest.TestCase):
    def setUp(self):
        self.lock = mock.Mock(spec=Lock)
        self.lock.acquire.return_value = self.lock
        self.cs = mock.Mock(
            spec=CollectionService,
            lock=self.lock,
        )
        self.context = mock.Mock(
            spec=CollectionContext,
            service=self.cs,
            method='GET',
        )

    def sr(self):
        return MyServiceRequest(self.context, [])

    def test_handle_lock(self):
        sr = self.sr()
        sr.handle()

        self.lock.acquire.assert_called_once_with()
        self.lock.release.assert_called_once_with()
