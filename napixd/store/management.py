#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import napixd
from napixd.store import Loader
from napixd.conf import ConfLoader
from napixd.conf.json import ConfFactory

conf_loader = ConfLoader([
    napixd.get_path('conf/'),
], ConfFactory())
loader = Loader(conf_loader())


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
