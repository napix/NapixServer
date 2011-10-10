#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Queue import Queue,Empty,Full

__all__ = ['Empty','Queue','Full','SubQueue','ThrowingSubQueue','ThrowingQueue']

# FIXME : Echec Critique ! L'absence de tout commentaire dans ce module provoque un AVC
#         chez votre chef qui lui font perdre toute notion de la valeur des monnaies.
#         Vous toucherez donc a présent votre salaire en rouble.

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
