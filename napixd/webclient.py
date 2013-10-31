#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
The webclient of Napixd.

Napixd propose a generic web client usable with  every server.
"""

from napixd.http.statics import StaticFiles


class WebClient(object):
    """
    An object to represent the Webclient.

    *root* is the path to the directory containing the index.html
    *launcher* is the :class:`napixd.launcher.Setup` class.
    """

    def __init__(self, root, launcher, generate_docs=True):
        self.service_name = launcher.service_name
        self._static = StaticFiles(root)

        if generate_docs:
            self.doc = launcher.doc
        else:
            self.doc = None

        if launcher.auth_handler:
            self.auth_server = getattr(launcher.auth_handler, 'host', '')
        else:
            self.auth_server = ''

        if launcher.notifier:
            self.directory_server = launcher.notifier.directory
        else:
            self.directory_server = None

    def setup_bottle(self, app):
        router = app.push()
        router.route('/_napix_js/', self.index, catchall=True)
        router.route('/_napix_js/infos.json', self.infos)
        if self.doc:
            router.route('/_napix_js/docs.json', self.docs)

    def index(self, request, path):
        """
        Returns the index.
        """
        path = path or 'index.html'
        return self._static(request, path)

    def docs(self):
        return self.doc.generate()

    def infos(self, request):
        """
        Returns informations about the server to the client.

        Those informations are extracted from the *launcher*
        """
        return {
            'name': self.service_name,
            'auth_server': self.auth_server,
            'directory_server': self.directory_server,
        }
