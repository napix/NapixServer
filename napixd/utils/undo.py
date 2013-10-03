#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging

logger = logging.getLogger('Napix.undo')


class UndoManager(object):
    """
    A class to watch a piece of code and register
    callbacks in case of an exception.

    If an exception is thrown during the execution of the context manager or
    by manually calling :meth:`undo`, all the callbacks are called in the
    reverse order in which they have been :meth:`registered<register>`.
    """
    def __init__(self):
        self._stack = []

    def undo(self):
        """
        Runs the error callbacks.

        If the callback raises an exception, it is ignored.
        """
        for callback in reversed(self._stack):
            try:
                callback()
            except Exception as e:
                logger.exception(e)

    def register(self, callback):
        """
        Registers a *callback*
        """
        self._stack.append(callback)
        return callback

    def __enter__(self):
        return self

    def __exit__(self, exc_value, exc_type, tb):
        if exc_value:
            self.undo()
