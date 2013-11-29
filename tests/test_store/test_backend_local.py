#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.store.backends import local
from tests.test_store.base import _BaseTestCounter


class TestLocalCounter(_BaseTestCounter):
    counter_class = local.LocalBackend()
