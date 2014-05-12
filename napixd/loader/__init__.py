#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Modules loader for napix.

A :class:`loader.Loader` instance finds and keeps tracks of modules
for the duration of the server.

It uses :class:`importers.Importer` subclasses to find the its managers.
"""

from napixd.loader.loader import Loader


__all__ = [
    'Loader',
]
