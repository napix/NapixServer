#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The Documentation generator.
"""

from napixd.docs.templates import LoaderDocTemplate


class DocGenerator(object):
    """
    A class that hosts the doc generator.

    *loader* is a :class:`napixd.loader.loader.Loader` instance.
    """
    def __init__(self, loader):
        self.loader = loader

    def generate(self):
        """
        Generate the doc and returns it as a dict.
        """
        t = LoaderDocTemplate(self.loader)
        return t.render({})
