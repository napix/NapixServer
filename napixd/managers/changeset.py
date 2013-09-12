#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections


class ChangeSet(collections.Mapping):

    def __init__(self, orig, patches):
        self.orig = orig
        self.patches = patches
        self.merge = dict(orig)
        self.merge.update(patches)
        for key in self.deleted_fields:
            del self.merge[key]

    def __iter__(self):
        return iter(self.merge)

    def __getitem__(self, key):
        return self.merge[key]

    def __len__(self):
        return len(self.merge)

    @property
    def new_fields(self):
        return set(self.patches).difference(self.orig)

    @property
    def deleted_fields(self):
        return set(self.orig).difference(self.patches)

    @property
    def changes(self):
        keys = set(self.orig).intersection(self.merge)
        return set(key for key in keys if self.orig[key] != self.merge[key])
