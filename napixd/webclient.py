#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
The webclient of Napixd.

Napixd propose a generic web client usable with  every server.
"""

import bottle

from napixd.plugins.conversation import ConversationPlugin


class WebClient(bottle.Bottle):
    """
    An object to represent the Webclient.

    *root* is the path to the directory containing the index.html
    *launcher* is the :class:`napixd.launcher.Setup` class.
    """

    def __init__(self, root, launcher, generate_docs=True):
        super(WebClient, self).__init__(autojson=False)
        self.root = root
        self.service_name = launcher.service_name
        self.doc = launcher.doc

        if launcher.auth_handler:
            self.auth_server = getattr(launcher.auth_handler, 'host', '')
        else:
            self.auth_server = ''

        if launcher.notifier:
            self.directory_server = launcher.notifier.directory
        else:
            self.directory_server = None

        self.get('/', callback=self.index)
        self.get('/<filename:path>', callback=self.static)
        self.get('/infos.json', callback=self.infos, apply=[
            ConversationPlugin()
        ])

        if generate_docs:
            self.get('/docs.json', callback=self.generate_docs, apply=[
                ConversationPlugin()
            ])

    def generate_docs(self):
        return self.doc.generate()

    def setup_bottle(self, app):
        app.mount('/_napix_js', self)

    def index(self):
        """
        Returns the index.
        """
        return bottle.static_file('index.html', root=self.root,
                                  mimetype='text/html; charset=UTF-8')

    def static(self, filename):
        """
        Returns the medias related to index.html.
        """
        return bottle.static_file(filename, root=self.root)

    def infos(self):
        """
        Returns informations about the server to the client.

        Those informations are extracted from the *launcher*
        """
        return {
            'name': self.service_name,
            'auth_server': self.auth_server,
            'directory_server': self.directory_server,
        }
