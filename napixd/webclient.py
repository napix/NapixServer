#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bottle

class WebClient( bottle.Bottle):
    def __init__(self, root):
        super( WebClient, self).__init__( autojson=False)
        self.root = root
        self.get('/', callback=self.index)
        self.get('/<filename:path>', callback=self.static)

    def setup_bottle(self, app):
        app.mount( '/_napix_js', self)

    def index(self):
        return bottle.static_file( 'index.html', root=self.root,
                mimetype = 'text/html; charset=UTF-8')

    def static(self, filename):
        return bottle.static_file( filename, root=self.root )
