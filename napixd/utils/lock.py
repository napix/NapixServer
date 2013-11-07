#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Management of locks
===================

Locks may be shared between napix instances, assuming they use the same Redis
Server to store the locks.


Redis mechanisms
----------------

A lock consists of two keys: a list and a string value.
The string value determines if the lock exists or not.
The list is a structure managed by redis where the clients
wait for a item to be inserted.

The lists have a blocking command :meth:`redis.Redis.brpop`
that blocks the receiver until a element is pushed.
The wait queue is handled by the redis server,
feeding the first to wait in first.

The control key, determine if a lock does not exists
or if its an empty list, meaning a held lock.

"""

import time
import functools
import threading

__all__ = ('synchronized', 'Lock', 'Timeout')

# The prefix for all the redis lists
PREFIX = 'napixd:locks:queues:'
# The prefix for all redis values that control the existense of the queues
CONTROL_PREFIX = 'napixd:locks:control:'


def synchronized(lock):
    """
    Decorator for synchronized methods/functions.

    The *lock* argument is a :class:`Lock` instance,
    or the name given to a :class:`Lock` to create a new instance.
    In this case, the kw are also given to the constructor.

    A same lock instance is reentrant,
    but two separate locks with the same name are not.

    >>> lock = Lock('l1')
    >>> @synchronized(lock)
    ... def nested():
    ...     pass

    >>> @synchronized(lock)
    ... def same_instance():
    ...     nested()

    >>> @synchronized('l1')
    ... def same_name():
    ...     nested()

    Here, :meth:`same_instance` and :meth:`nested` share the same
    :class:`Lock` instance.
    Thus :meth:`same_instance` can call :meth:`nested` whithout blocking.

    Whereas :meth:`same_name` and :meth:`nested` share the same lock name.
    When :meth:`same_name` calls :meth:`nested` it will block because the lock
    is held.
    """
    if not isinstance(lock, Lock):
        raise ValueError('lock should be a Lock instance')

    def decorator(fn):
        @functools.wraps(fn)
        def inner_synchronize(*args, **kw):
            with lock:
                return fn(*args, **kw)
        return inner_synchronize
    return decorator


class Timeout(Exception):
    """
    An exception meaning that a call to :meth:`Lock.acquire` took
    more than the specified timeout to complete.
    """
    pass


class Lock(object):
    """
    A lock class.

    Locking prevent simultaneous access to shared resources.

    A lock is :meth:`acquired<acquire>` before the critical section.
    This method can block if the lock is held by another process.

    Once the critical section has finished, the lock should always be
    :meth:`released<release>`.
    A ``finally`` block is recommended.

    >>> lock = Lock('l1')
    >>> lock.acquire()
    >>> try:
    ...     pass  # Critical section
    ... finally:
    ...     lock.release()

    The lock can be used as a context manager.
    The lock is acquired at the enter and released at the end.

    The lock is reentrant whith the same lock instance.
    Once a lock instance is acquired, all subsequent acquisition
    is automatically granted.

    >>> instance_a = Lock('l1')
    >>> instance_a.acquire()
    >>> instance_a.acquire()  # The lock is acquired

    >>> instance_b = Lock('l1')
    >>> instance_b.acquire() # this will block.

    For every call to :meth:`aquire` a call to :meth:`release` must be issued.

    A lock object will evaluate to True if it holds the lock.

    >>> l = Lock('l1')
    >>> bool(l)
    False
    >>> l.acquire()
    >>> bool(l)
    True

    .. attribute:: expire

        The maximum time a lock is held.
        When a process examining a lock see that it was not released since
        at least *expire* seconds, it can assume that it died without releasing
        the resource and acquire it.
    """
    def __init__(self, name, conn, expire=60):
        if isinstance(name, Lock):
            name = name.name

        self.name = name
        self.conn = conn
        self.key = PREFIX + name
        self.control = CONTROL_PREFIX + name
        self.expire = expire
        self._owner = None
        self._acquired = 0
        self._acquired_until = None

    def _clean(self):
        self.conn.delete(self.key)
        self.conn.delete(self.control)

    def _init_lock(self, pipe):
        if not pipe.exists(self.control):
            pipe.multi()
            pipe.delete(self.key)
            pipe.rpush(self.key, 1)
            pipe.set(self.control, 1)

    def acquire(self, blocking=True, timeout=5):
        """
        Acquires the lock and returns it.

        The *blocking* parameter defines the behavior when the lock
        is not available.
        When *blocking* is True, the acquisition may take up to
        *timeout* seconds or raise a :exc:`Timeout`.

        When it's False, the method will return immediately without
        acquiring the lock.
        In such cases, :meth:`release` must no be called.

        The lock is returned, and as it evaluates to bool only if the lock
        is acquired, it can be used directly in a ``if`` statement.

        >>> if lock.acquire(blocking=False):
        ...     try:
        ...         pass  # do something with the lock
        ...     finally:
        ...         lock.release()
        ... else:
        ...     print 'The lock was not available'

        .. note::

                The call with the context manager are always blocking.
        """
        if self.owned:
            if self._acquired == 0:
                raise RuntimeError('Reentering in a non-acquired lock')

            self._acquired += 1
            return self

        self.conn.transaction(self._init_lock, self.control)
        if blocking:
            acquired = self.conn.brpop(self.key, timeout=int(timeout))
        else:
            acquired = self.conn.rpop(self.key)

        if acquired is None:
            if blocking:
                raise Timeout()
        else:
            self._owner = threading.current_thread()
            self._acquired_until = until = time.time() + self.expire
            self.conn.expireat(self.key, int(until))

            self._acquired += 1
        return self

    def release(self):
        """
        Releases the lock.

        The lock is returned.
        This allow to cast as a bool to check if the lock is still held.

        >>> if lock.release():
        ...     print 'The lock is still held'
        ... else:
        ...     print 'The lock is not held'
        """
        if not self.owned:
            raise RuntimeError('Releasing a non-owned lock')

        if self._acquired == 0:
            raise RuntimeError('Releasing a non-acquired lock')

        self._acquired -= 1
        if self._acquired == 0:
            self._owner = None
            if time.time() < self._acquired_until:
                self.conn.rpush(self.key, 1)

        return self

    @property
    def owned(self):
        return self._owner is not None and self._owner == threading.current_thread()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.release()

    def __nonzero__(self):
        return self.owned and bool(self._acquired)
