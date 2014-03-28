#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock

from napixd.utils.lock import Lock

from napixd.services.collection import CollectionService
from napixd.services.context import CollectionContext

from napixd.services.requests.base import ServiceRequest


class MyServiceRequest(ServiceRequest):
    def call(self):
        return None

    def serialize(self, value):
        return None


class TestServiceRequest(unittest.TestCase):
    def setUp(self):
        self.cs = mock.Mock(
            spec=CollectionService,
            lock=mock.Mock(spec=Lock),
        )
        self.context = mock.Mock(
            spec=CollectionContext,
            service=self.cs,
            method='GET',
        )
        self.context.get_manager.return_value = mock.Mock()

    def sr(self):
        return MyServiceRequest(self.context, [])

    def test_handle_lock(self):
        lock = self.cs.lock
        sr = self.sr()
        sr.handle()

        lock.acquire.assert_called_once_with()
        lock.release.assert_called_once_with()
