#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    import django
except ImportError:
    django = None

if django:
    from tests.test_connectors.django_import import *
    from tests.test_connectors.django_manager import *
