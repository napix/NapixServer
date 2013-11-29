#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections


class DiffDict(collections.MutableMapping):
    """
    A mapping that keeps tracks of the changes between a source
    and a patch.

    *orig* is a mapping that is used a source and *patches* is a mapping
    used as a destination.

    >>> c = DiffDict({'a': 1, 'c': 3}, {'a': 2, 'b': 2})
    >>> c['a'], c['b'], c.get('c')
    (2, 2, None)
    """

    def __init__(self, orig, patches):
        self.orig = orig
        self.patches = patches
        self.merge = dict(orig)
        self.merge.update(patches)
        for key in self.deleted:
            del self.merge[key]

    def __iter__(self):
        return iter(self.merge)

    def __getitem__(self, key):
        return self.merge[key]

    def __len__(self):
        return len(self.merge)

    def __setitem__(self, key, value):
        self.patches[key] = value
        self.merge[key] = value

    def __delitem__(self, key):
        del self.patches[key]
        del self.merge[key]

    @property
    def added(self):
        """
        The :class:`set` of fields that are in *patches*
        and are not in *orig*.

        >>> c = DiffDict({'a': 1}, {'b': 2})
        >>> c.added
        set(['b'])
        """
        return set(self.patches).difference(self.orig)

    @property
    def deleted(self):
        """
        The :class:`set` of fields that are no more in *patches*
        and are in *orig*.

        >>> c = DiffDict({'a': 1}, {'b': 2})
        >>> c.deleted
        set(['a'])
        """
        return set(self.orig).difference(self.patches)

    @property
    def changed(self):
        """
        The :class:`set` of fields where the value was both in *orig* and
        *patches* and changed.

        >>> c = DiffDict({'a': 1, 'b': 2}, {'a': 2, 'b': 2})
        >>> c.changed
        set(['a'])
        """
        keys = set(self.orig).intersection(self.merge)
        return set(key for key in keys if self.orig[key] != self.merge[key])
