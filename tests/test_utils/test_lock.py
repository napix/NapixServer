#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import gevent
import redis.connection

from napixd.utils.lock import Lock, Timeout


old_socket = None


def setUpModule():
    global old_socket
    old_socket = redis.connection.socket
    redis.connection.socket = gevent.socket


def tearDownModule():
    redis.connection.socket = old_socket


hub = gevent.get_hub()


class TestLock(unittest.TestCase):
    def setUp(self):
        self.lock1 = Lock('l1')
        self.lock1._clean()
        self.lock2 = Lock('l1')

    def test_acquire(self):
        # L1      |     L2
        # Acquire |
        #         | Acquire
        # Release | Acquire

        timeline = []

        def thread1():
            timeline.append(1)
            self.lock1.acquire()
            timeline.append(2)
            gevent.sleep(0)
            timeline.append(3)
            self.lock1.release()

        def thread2():
            self.lock2.acquire()
            timeline.append(4)
            gevent.sleep(0)
            timeline.append(5)
            self.lock2.release()

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
            self.lock1.acquire()
            timeline.append(2)
            gevent.sleep(0)
            timeline.append(3)
            self.lock1.acquire()
            gevent.sleep(0)
            timeline.append(4)
            self.lock1.release()
            timeline.append(5)
            self.lock1.release()

        def thread2():
            self.lock2.acquire()
            timeline.append(6)
            gevent.sleep(0)
            timeline.append(7)
            self.lock2.release()

        g1 = gevent.spawn(thread1)
        g2 = gevent.spawn(thread2)

        gevent.joinall([g1, g2])

        self.assertEqual(timeline, [1, 2, 3, 4, 5, 6, 7])

    def test_context_manager(self):
        self.assertFalse(bool(self.lock1))
        with self.lock1 as l:
            self.assertTrue(self.lock1 is l)
            self.assertTrue(bool(self.lock1))
        self.assertFalse(bool(self.lock1))

    def test_non_blocking(self):
        state = 'free'

        def thread1():
            global state
            self.lock1.acquire()
            state = 'thread1'
            while state == 'thread1':
                gevent.sleep(0)
            self.lock1.release()

        def thread2():
            global state
            while state != 'thread1':
                gevent.sleep(0)
            l2 = self.lock2.acquire(blocking=False)
            lock_bool_value = bool(l2)
            state = 'thread2'
            self.assertFalse(lock_bool_value)

        g1 = gevent.spawn(thread1)
        g2 = gevent.spawn(thread2)

        with gevent.Timeout(.1):
            g1.get()
            g2.get()

    def test_blocking_acquire(self):
        self.lock2.acquire(blocking=False)
        self.assertTrue(bool(self.lock2))
        self.lock2.release()

    def test_timeout(self):
        with self.lock1:
            self.assertRaises(Timeout, self.lock2.acquire, timeout=1)
