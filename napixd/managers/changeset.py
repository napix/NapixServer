#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections


class ChangeSet(collections.Mapping):
    """
    A mapping that keeps tracks of the changes between a source
    and a patch.

    *orig* is a mapping that is used a source and *patches* is a mapping
    used as a destination.

    >>> c = ChangeSet({'a': 1, 'c': 3}, {'a': 2, 'b': 2})
    >>> c['a'], c['b'], c.get('c')
    (2, 2, None)
    """

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
        """
        The :class:`set` of fields that are in *patches*
        and are not in *orig*.

        >>> c = ChangeSet({'a': 1}, {'b': 2})
        >>> c.new_fields
        set(['b'])
        """
        return set(self.patches).difference(self.orig)

    @property
    def deleted_fields(self):
        """
        The :class:`set` of fields that are no more in *patches*
        and are in *orig*.

        >>> c = ChangeSet({'a': 1}, {'b': 2})
        >>> c.deleted_fields
        set(['a'])
        """
        return set(self.orig).difference(self.patches)

    @property
    def changes(self):
        """
        The :class:`set` of fields where the value was both in *orig* and
        *patches* and changed.

        >>> c = ChangeSet({'a': 1, 'b': 2}, {'a': 2, 'b': 2})
        >>> c.changes
        set(['a'])
        """
        keys = set(self.orig).intersection(self.merge)
        return set(key for key in keys if self.orig[key] != self.merge[key])
