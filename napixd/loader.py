#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger('Napix.loader')

import sys
from .conf import Conf
from .services import Service

import bottle
from .plugins import ConversationPlugin


def get_bottle_app():
    napixd = NapixdBottle()
    napixd.install(ConversationPlugin())
    return napixd


class NapixdBottle(bottle.Bottle):
    def __init__(self):
        super(NapixdBottle,self).__init__(autojson=False)#,catchall=False)
        self.services = list(self._load_services())
        for service in self.services:
            service.setup_bottle(self)
        self.route('/',callback=self.slash)
        self.error(404)(self.not_found)
        self.error(400)(self.bad_request)

    def _load_managers(self):
        managers_conf = Conf.get_default().get('Napix.managers')
        for manager_path,managers in managers_conf.items():
            __import__(manager_path)
            logger.debug('import %s',manager_path)
            for manager_name in managers:
                manager = getattr(sys.modules[manager_path],manager_name)
                logger.debug('load %s',manager_name)
                yield manager

    def _load_services(self):
        for manager in self._load_managers():
            config = Conf.get_default().get(manager.get_name())
            service = Service(manager,config)
            logger.debug('service %s',service.url)
            yield service

    def slash(self):
        return ['/'+x.url for x in self.services ]
    def not_found(self,e):
        return bottle.HTTPResponse(e.output,
                status=404,header=[('Content-type','text/plain')])
    def bad_request(self,e):
        return bottle.HTTPResponse(e.output,
                status=400,header=[('Content-type','text/plain')])

