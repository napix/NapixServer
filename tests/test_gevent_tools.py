#!/usr/bin/env python
# -*- coding: utf-8 -*-




import time
import unittest
import gevent

from napixd.gevent_tools import Chrono, Greenlet, Tracer, AddGeventTimeHeader

class TestChrono(unittest.TestCase):
    def test_chrono(self):
        chrono = Chrono()
        with chrono:
            time.sleep(.1)
        self.assertAlmostEquals( chrono.total, .1, places = 2)

    def test_chrono_exception(self):
        chrono = Chrono()
        try:
            with chrono:
                time.sleep(.1)
                raise Exception
        except :
            pass
        self.assertAlmostEquals( chrono.total, .1, places = 2)

class TestTimedGreenlet(unittest.TestCase):
    def setUp(self):
        self.greenlet = Greenlet()

    def test_no_times(self):
        self.assertEquals( self.greenlet.get_running_time(), 0)

    def test_running(self):
        self.greenlet.add_time()
        time.sleep(.1)
        self.greenlet.add_time()
        self.assertAlmostEquals( self.greenlet.get_running_time(), .1, places=2)

    def test_running_and_yielding(self):
        self.greenlet.add_time()
        time.sleep(.1) # running
        self.greenlet.add_time()
        time.sleep(.1) # not running
        self.greenlet.add_time()
        time.sleep(.1) # running
        self.greenlet.add_time()
        self.assertAlmostEquals( self.greenlet.get_running_time(), .2, places=2)


class TestTracer(unittest.TestCase):
    def setUp(self):
        self.tracer = Tracer()
        self.tracer.set_trace()
    def tearDown(self):
        self.tracer.unset_trace()

    def test_yield(self):
        def x1():
            #first step
            gevent.sleep(.1)
            #second step
            g2.join()
            #third step
        def x2():
            #first step
            gevent.sleep(.1)
            #second step

        g1 = Greenlet.spawn( x1)
        g2 = Greenlet.spawn( x2)

        g1.join()

        self.assertEquals( len( list( g1.get_running_intervals())), 3)
        self.assertEquals( len( list( g2.get_running_intervals())), 2)

class Resp(object):
    def __init__(self):
        self.headers = {}

class TestGeventHeaders(unittest.TestCase):

    def _do_something(self):
        """This function should run in .1s with a total run of .2s"""
        gevent.sleep( 0.1) #Yield
        time.sleep( 0.1) #No Yield
        return Resp()

    def setUp(self):
        self.plugin = AddGeventTimeHeader()
        self.callback = self.plugin.apply( self._do_something, None)

    def test_run_solo( self):
        resp = self.callback()
        self.assertAlmostEquals( resp.headers['x-total-time'], .2, places=1)
        self.assertAlmostEquals( resp.headers['x-running-time'], .1, places=1)

    def test_run(self):
        resps = [ self.callback() for x in xrange(4) ]
        for resp in resps:
            self.assertAlmostEquals( resp.headers['x-total-time'], .2, places=1)
            self.assertAlmostEquals( resp.headers['x-running-time'], .1, places=1)


