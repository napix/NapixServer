#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.docs.templates import LoaderDocTemplate


class DocGenerator(object):
    def __init__(self, loader):
        self.loader = loader

    def generate(self):
        t = LoaderDocTemplate(self.loader)
        return t.render({})
