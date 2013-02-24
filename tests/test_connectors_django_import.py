#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
import napixd
try:
    import django
    from napixd.connectors.django import DjangoImport
except ImportError:
    django = None


@unittest2.skipIf( django is None, 'Missing django dependency')
class TestDjangoImport( unittest2.TestCase ):
    @classmethod
    def setUpClass( self):
        if django is None:
            return
        conf_ = reload(django.conf)
        napixd.connectors.django.settings = conf_.settings

    def tearDown(self):
        django_ = reload(django)
        conf_ = reload(django.conf)
        napixd.connectors.django.django = django_
        napixd.connectors.django.settings = conf_.settings

    def test_import_module(self):
        with DjangoImport('tests.mock.django_settings'):
            from django.conf import settings

        self.assertEqual( settings.MY_SETTING, 1)

    def test_import_dict( self):
        with DjangoImport({ 'MY_SETTING' : 2 }):
            from django.conf import settings

        self.assertEqual( settings.MY_SETTING, 2)

    def test_reimport_same_dict(self):
        with DjangoImport({ 'MY_SETTING' : 3 }):
            from django.conf import settings
        with DjangoImport({ 'MY_SETTING' : 3 }):
            from django.conf import settings as re_settings

        self.assertEqual( settings.MY_SETTING, 3)
        self.assertEqual( re_settings.MY_SETTING, 3)

    def test_reimport_not_same_dict(self):
        with DjangoImport({ 'MY_SETTING' : 4 }):
            from django.conf import settings
        def try_import():
            with DjangoImport({ 'MY_SETTING' : 5 }):
                from django.conf import settings as re_settings
        self.assertRaises( RuntimeError, try_import)

