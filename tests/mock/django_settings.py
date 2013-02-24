#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path

MY_SETTING = 1

DATABASES = {
        'default' : {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join( os.path.dirname(__file__), "sqlitedb"),
            }
        }

SECRET_KEY = 'oo'


