#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger('Napix.loader')

import sys
from .conf import Conf
from .services import Service

import bottle
from .plugins import ConversationPlugin


def _load_managers():
    managers_conf = Conf.get_default().get('Napix.managers')
    for manager_path,managers in managers_conf.items():
        __import__(manager_path)
        logger.debug('import %s',manager_path)
        for manager_name in managers:
            manager = getattr(sys.modules[manager_path],manager_name)
            logger.debug('load %s',manager_name)
            yield manager

def _load_services():
    for manager in _load_managers():
        config = Conf.get_default().get(manager.get_name())
        service = Service(manager,config)
        logger.debug('service %s',service.url)
        yield service

def get_bottle_app():
    napixd = bottle.Bottle(autojson=False)
    napixd.autojson=False

    services = list(_load_services())
    for service in services:
        service.setup_bottle(napixd)

    @napixd.route('/')
    def slash():
        return ['/'+x.url for x in services ]

    @napixd.error(404)
    def not_found(e):
        return bottle.HTTPResponse(status=404,header=[('Content-type','text/plain')])

    @napixd.error(400)
    def bad_request(e):
        return bottle.HTTPResponse(e.output,
                status=404,header=[('Content-type','text/plain')])


    napixd.install(ConversationPlugin())
    return napixd
