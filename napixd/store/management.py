#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from napixd.store import loader


def load(fd, backend, reset=False):
    store = loader.get_store_backend(backend)
    if reset:
        store.drop()
    document = json.load(fd)
    store.load(document)


def dump(backend, fd, indent):
    store = loader.get_store_backend(backend)
    document = store.dump()
    json.dump(document, fd, indent=indent)


def move(source_backend, dest_backend, reset=False):
    source = loader.get_store_backend(source_backend)
    destination = loader.get_store_backend(dest_backend)

    if reset:
        destination.drop()

    destination.load(source.dump())
