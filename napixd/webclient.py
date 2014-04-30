#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
The webclient of napixd.

Napixd propose a generic web client usable with every server.
"""

from napixd.http.statics import StaticFiles


class WebClient(object):
    """
    An object to represent the Webclient.

    *root* is the path to the directory containing the index.html and *launcher*
    is the :class:`napixd.launcher.Setup` class.
    """

    def __init__(self, root, infos, docs=None, index='index.html'):
        self._static = StaticFiles(root)
        self._index = index
        self._infos = infos
        self.doc = docs

    def setup_bottle(self, app):
        router = app.push()
        router.route('/_napix_js/', self.index, catchall=True)
        router.route('/_napix_js/infos.json', self.infos)
        if self.doc:
            router.route('/_napix_js/docs.json', self.docs)

    def index(self, request, path):
        """
        View for the static pages.

        Returns the *index* if path is empty.
        """
        path = path or self._index
        return self._static(request, path)

    def docs(self, request):
        """
        View of the documentation.
        """
        return self.doc.generate()

    def infos(self, request):
        """
        Returns informations about the server to the client.

        Those informations are extracted from the *launcher*.
        """
        return self._infos
