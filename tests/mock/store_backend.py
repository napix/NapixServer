#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mock

from napixd.store.backends import BaseBackend


class MockBackend(BaseBackend):
    return_value = mock.Mock()

    def __new__(self, options):
        return self.return_value
