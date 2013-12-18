#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib


class URL(object):
    """
    An abstraction class for URLs with arguments.

    URL are build from *segments*
    The segments are either a string or :obj:`None`

    The objects are converted to :mod:`bottle` compatible
    rules for urls by calling :class:`unicode` on it.
    """

    def __init__(self, segments=None):
        self.segments = segments or []

    def __eq__(self, other):
        return isinstance(other, URL) and self.segments == other.segments

    @classmethod
    def _from(cls, orig, addition):
        segments = list(orig.segments)
        segments.append(addition)
        return cls(segments)

    def add_segment(self, value):
        """
        Returns a new :class:`URL` with a defined *value* segment at the end.
        """
        return self._from(self, value)

    def add_variable(self):
        """
        Returns a new :class:`URL` with an expected argument.
        """
        return self._from(self, None)

    def __unicode__(self):
        if not self.segments:
            return u'/'
        urls = ['']
        for segment in self.segments:
            if segment is None:
                urls.append('?')
            else:
                urls.append(segment)
        return u'/'.join(urls)

    def _quote(self, value):
        return urllib.quote(unicode(value), '')

    def reverse(self, ids):
        """
        Returns a unicode string of this url with the expected
        values replaced by the values of *ids*

        The values of *ids* are quoted.

        >>> u = URL(['ab', None, 'cd', None])
        >>> u.reverse([ 'value1', 'val ue2'])
        u'/ab/value1/cd/val%20ue2'
        """
        urls = ['']
        ids = iter(ids)
        for segment in self.segments:
            if segment is None:
                urls.append(self._quote(next(ids)))
            else:
                urls.append(segment)
        for id in ids:
            urls.append(self._quote(id))
        return u'/'.join(urls)

    def with_slash(self):
        """
        Returns the unicode value of this url with a trailling slash.
        """
        return unicode(self) + u'/'

    def __repr__(self):
        return '<URL {0}>'.format(unicode(self))
