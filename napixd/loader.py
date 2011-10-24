#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
from ConfigParser import SafeConfigParser

logger = logging.getLogger('Napix.loader')

def load_path(managers_path):
    __import__(managers_path)
    module = sys.modules[managers_path]

    istype = lambda x:isinstance(x,type)
    classes = [ getattr(module,x) for x in getattr(module,'__all__',dir(module)) if istype(x) ]
    logger.debug('Found %s in %s',classes,managers_path)
    return classes


def load_managers(managers_pathes):
    managers = set()
    for managers_path in managers_pathes:
        managers.update(load_path(managers_path))
    return managers

def load(pathes,blacklisted,forced):
    blacklisted = set(blacklisted)
    forced = set(forced)

    for manager in load_path(pathes):
        if manager.__name__ in blacklisted:
            logger.debug('Ignore blacklisted %s',manager.__name__)
            continue
        if manager.__name__ in forced:
            logger.debug('Propose %s',manager.__name__)
            yield manager
            continue
        if hasattr(manager,'detect'):
            if manager.detect():
                logger.debug('Detected %s',manager.__name__)
                yield manager

default_conf = SafeConfigParser()
default_conf.read(['/etc/napixd/settings.ini','/home/cecedille1/enix/napix/server/napixd/conf/settings.ini'])

def load_conf(manager):
    if default_conf.has_section(manager.lower()):
        return dict(default_conf.items(manager))
    return {}
