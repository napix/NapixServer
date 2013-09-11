#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib


class URL(object):
    def __init__(self, segments=None):
        self.segments = segments or []

    def add_segment(self, value):
        segments = list(self.segments)
        segments.append(value)
        return URL(segments)

    def add_variable(self):
        segments = list(self.segments)
        segments.append(None)
        return URL(segments)

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
