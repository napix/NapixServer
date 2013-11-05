#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import gevent
import threading
import redis.connection

from napixd.utils.lock import Lock, Timeout


old_socket = None
old_current_thread = None


def setUpModule():
    global old_socket, old_current_thread
    old_socket = redis.connection.socket
    redis.connection.socket = gevent.socket

    old_current_thread = threading.current_thread
    threading.current_thread = gevent.getcurrent


def tearDownModule():
    redis.connection.socket = old_socket
    threading.current_thread = old_current_thread


class TestLock(unittest.TestCase):
    def setUp(self):
        self.lock = Lock('l1', redis.Redis())
        self.lock._clean()

    def test_acquire(self):
        # L1      |     L2
        # Acquire |
        #         | Acquire
        # Release | Acquire

        timeline = []

        def thread1():
            timeline.append(1)
            self.lock.acquire()
            timeline.append(2)
            gevent.sleep(0)
            timeline.append(3)
            self.lock.release()

        def thread2():
            self.lock.acquire()
            timeline.append(4)
            gevent.sleep(0)
            timeline.append(5)
            self.lock.release()

        g1 = gevent.spawn(thread1)
        g2 = gevent.spawn(thread2)

        gevent.joinall([g1, g2])

        self.assertEqual(timeline, [1, 2, 3, 4, 5])

    def test_acquire_reentrant(self):
        # L1      |     L2
        # Acquire |
        #         | Acquire
        # Release | Acquire

        timeline = []

        def thread1():
            timeline.append(1)
            self.lock.acquire()
            timeline.append(2)
            gevent.sleep(0)
            timeline.append(3)
            self.lock.acquire()
            gevent.sleep(0)
            timeline.append(4)
            self.lock.release()
            timeline.append(5)
            self.lock.release()

        def thread2():
            self.lock.acquire()
            timeline.append(6)
            gevent.sleep(0)
            timeline.append(7)
            self.lock.release()

        g1 = gevent.spawn(thread1)
        g2 = gevent.spawn(thread2)

        gevent.joinall([g1, g2])

        self.assertEqual(timeline, [1, 2, 3, 4, 5, 6, 7])

    def test_context_manager(self):
        self.assertFalse(bool(self.lock))
        with self.lock as l:
            self.assertTrue(self.lock is l)
            self.assertTrue(bool(self.lock))
        self.assertFalse(bool(self.lock))

    def test_non_blocking(self):
        state = 'free'

        def thread1():
            global state
            self.lock.acquire()
            state = 'thread1'
            while state == 'thread1':
                gevent.sleep(0)
            self.lock.release()

        def thread2():
            global state
            while state != 'thread1':
                gevent.sleep(0)
            l2 = self.lock.acquire(blocking=False)
            lock_bool_value = bool(l2)
            state = 'thread2'
            self.assertFalse(lock_bool_value)

        g1 = gevent.spawn(thread1)
        g2 = gevent.spawn(thread2)

        with gevent.Timeout(.1):
            g1.get()
            g2.get()

    def test_blocking_acquire(self):
        self.lock.acquire(blocking=False)
        self.assertTrue(bool(self.lock))
        self.lock.release()

    def test_timeout(self):
        def fn():
            try:
                self.lock.acquire(timeout=1)
                self.lock.release()
                return True
            except Timeout:
                return False

        with gevent.Timeout(2):
            with self.lock:
                gl = gevent.spawn(fn)
                self.assertFalse(gl.get())
