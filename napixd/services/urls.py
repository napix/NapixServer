#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib


class URL(object):
    def __init__(self, segments=None):
        self.segments = segments or []

    @classmethod
    def _from(cls, orig, addition):
        segments = list(orig.segments)
        segments.append(addition)
        return cls(segments)

    def add_segment(self, value):
        return self._from(self, value)

    def add_variable(self):
        return self._from(self, None)

    def __unicode__(self):
        if not self.segments:
            return u'/'
        urls = ['']
        count = 0
        for segment in self.segments:
            if segment is None:
                urls.append(':f{0}'.format(count))
                count += 1
            else:
                urls.append(segment)
        return u'/'.join(urls)

    def reverse(self, ids):
        urls = ['']
        ids = iter(ids)
        for segment in self.segments:
            if segment is None:
                urls.append(urllib.quote(unicode(next(ids)), ''))
            else:
                urls.append(segment)
        return u'/'.join(urls)

    def with_slash(self):
        return unicode(self) + u'/'

    def __repr__(self):
        return '<URL {0}>'.format(unicode(self))
