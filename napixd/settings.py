#!/usr/bin/env python
# -*- coding: utf-8 -*-

DEBUG = True

#Daemon configuration
HOST = '127.0.0.9'
PORT = 8080

#Path where managers can be found
MANAGERS_PATH = ['example.list_manager']
#Managers to force
MANAGERS = ['HostManager']

#Managers that should not be loaded
BLACKLIST = []

#
SERVICE = ''
AUTH_URL = 'http://auth.napix.local/auth/authorization/'
