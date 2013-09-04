#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bottle

from napixd.plugins import ConversationPlugin

class WebClient( bottle.Bottle):
    def __init__(self, root, launcher):
        super( WebClient, self).__init__(autojson=False)
        self.root = root
        self.service_name = launcher.service_name

        if launcher.auth_handler:
            self.auth_server = getattr(launcher.auth_handler, 'host', '')
        else:
            self.auth_server = ''

        self.get('/', callback=self.index)
        self.get('/<filename:path>', callback=self.static)
        self.get('/infos.json', callback=self.infos, apply=[
            ConversationPlugin()
        ])


    def setup_bottle(self, app):
        app.mount( '/_napix_js', self)

    def index(self):
        return bottle.static_file( 'index.html', root=self.root,
                mimetype = 'text/html; charset=UTF-8')

    def static(self, filename):
        return bottle.static_file( filename, root=self.root )

    def infos(self):
        return {
            'name': self.service_name,
            'auth_server': self.auth_server,
        }
