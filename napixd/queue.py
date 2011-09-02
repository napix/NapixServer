#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Queue import Queue,Empty,Full

class SubQueueMixin:
    def __init__(self,main_queue):
        self.main_queue = main_queue
        Queue.__init__(self)
    def put(self,value):
        self.main_queue.put(value)
        Queue.put(self,value)

class ThrowingQueueMixin:
    def get(self,block=True,timeout=None):
        res=Queue.get(self,block,timeout)
        if isinstance(res,Exception):
            raise res
        return res

class ThrowingQueue(ThrowingQueueMixin,Queue):
    pass
class ThrowingSubQueue(ThrowingQueueMixin,SubQueueMixin,Queue):
    pass
class SubQueue(SubQueueMixin,Queue):
    pass
