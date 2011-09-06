#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
import time
from napixd.threadator import ThreadManager,BackgroundTasker

def sleepytask(thread):
    time.sleep(1)
def notthingtask(thread):
    return 555
def exceptiontask(thread):
    raise Exception,444

class TestThreadator(unittest.TestCase):
    def setUp(self):
        self.threadator = ThreadManager()
        self.threadator.start()
    def tearDown(self):
        self.threadator.stop()

    def testStarting(self):
        threadator = ThreadManager()
        start =time.time()
        threadator.start()
        self.assertAlmostEquals(time.time(),start,places=3)
        threadator.stop()
        self.assertLess(time.time(),start+3)

    def testAttributes(self):
        thread = self.threadator.do_async(notthingtask)
        self.assertTrue(hasattr(thread,'execution_state'))
        self.assertTrue(hasattr(thread,'status'))

    def testAsync(self):
        start=time.time()
        self.threadator.do_async(sleepytask)
        self.assertAlmostEquals(start,time.time(),places=1)

    def testStatusException(self):
        thread = self.threadator.do_async(exceptiontask)
        self.assertIsNotNone(thread)
        CREATED,RUNNING,RETURNED,EXCEPTION,FINISHING,CLOSED = range(6)
        for x in [ CREATED, RUNNING, EXCEPTION , FINISHING, CLOSED ] :
            _,ec = thread.execution_state_queue.get()
            self.assertEqual(ec,x)
    def testStatusSuccess(self):
        thread = self.threadator.do_async(notthingtask)
        self.assertIsNotNone(thread)
        CREATED,RUNNING,RETURNED,EXCEPTION,FINISHING,CLOSED = range(6)
        for x in [ CREATED, RUNNING, RETURNED, FINISHING, CLOSED ] :
            _,ec = thread.execution_state_queue.get()
            self.assertEqual(ec,x)
    def testCallbackSucess(self):
        results=[]
        self.threadator.do_async(notthingtask,
                on_failure=lambda ex:results.append(str('ex')),
                on_end=lambda :results.append(1),
                on_success=lambda x:results.append(x)).join()
        self.assertItemsEqual([555,1],results)
    def testCallbackException(self):
        results=[]
        self.threadator.do_async(exceptiontask,
                on_failure=lambda ex:results.append(str(ex)),
                on_end=lambda :results.append(1),
                on_success=lambda x:results.append(x)).join()
        self.assertItemsEqual(['444',1],results)

class TestBackgroundTasker(unittest.TestCase):
    def tearDown(self):
        self.threadator.stop()
    def setUp(self):
        self.threadator = ThreadManager()
        self.bgtasker = BackgroundTasker(self.threadator)
        self.threadator.start()

    def testAsync(self):
        @self.bgtasker
        def mpm():
            time.sleep(2)

        start= time.time()
        mpm()
        self.assertAlmostEquals(time.time(),start,places=2)

if __name__ == '__main__':
    unittest.main()
