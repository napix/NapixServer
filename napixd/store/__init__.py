#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
from ..conf import Conf

class NoSuchStoreBackend(Exception):
    pass

def fake_store_factory(backend, cause):
    def _fake_store(collection, **opts):
        raise NoSuchStoreBackend, 'there is no backend `%s` available because of %s' % ( backend, cause)
    return _fake_store

def load_backend_factory(default_location, default_class, conf_key):
    cache = {}
    def load_backend(backend):
        backend = backend or Conf.get_default(conf_key) or default_class
        if backend not in cache:
            if '.' in backend:
                module, dot, classname = backend.rpartition('.')
            else:
                module = default_location
                classname = backend
                backend = '%s.%s' % ( module, classname)
            try:
                __import__(module)
                cache[backend] = getattr( sys.modules[module], classname)
            except Exception as e:
                cache[backend] = fake_store_factory( backend, repr(e) )
        return cache[backend]
    return load_backend

store_loader = load_backend_factory( 'napixd.store.backends', 'FileStore', 'Napix.storage.store')
def Store(collection, backend=None, **opts):
    return store_loader(backend)( collection, **opts )

counter_loader = load_backend_factory( 'napixd.store.counters', 'LocalCounter', 'Napix.storage.counter')
def Counter( name, backend=None, **opts):
    return counter_loader(backend)( name, **opts)


