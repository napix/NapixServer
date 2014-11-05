#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mock

from napixd.store.backends import BaseBackend


class MockBackend(BaseBackend):
    return_value = mock.Mock()
    set_options = mock.Mock()

    def __new__(self, options):
        self.set_options(options)
        return self.return_value
