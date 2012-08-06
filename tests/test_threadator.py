#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
import time

from napixd.thread_manager import ThreadManager,BackgroundDecorator

def setUpModule():
    import logging
    logging.getLogger('Napix.thread_manager').addHandler(
            logging.StreamHandler(strm=open('/dev/null','w')))

def sleepytask():
    time.sleep(1)
def notthingtask():
    return 555
def exceptiontask():
    raise Exception,444
def itisathread( thread):
    thread.status = 'doing'
    return thread.execution_state

class TestThreadator(unittest.TestCase):
    def setUp(self):
        self.thread_manager = ThreadManager()
        self.thread_manager.start()
    def tearDown(self):
        self.thread_manager.stop()

    def testStarting(self):
        thread_manager = ThreadManager()
        start =time.time()
        thread_manager.start()
        self.assertAlmostEquals(time.time(),start,places=1)
        thread_manager.stop()
        self.assertTrue(time.time() < start+3)

    def testGivenThread(self):
        thread = self.thread_manager.do_async( itisathread, give_thread=True)
        thread.join()
        self.assertEqual( thread.status, 'doing')
        self.assertEqual( thread.result, 'RUNNING')

    def testAttributes(self):
        thread = self.thread_manager.do_async(notthingtask)
        self.assertTrue(hasattr(thread,'execution_state'))
        self.assertTrue(hasattr(thread,'status'))

    def testAsync(self):
        start=time.time()
        self.thread_manager.do_async(sleepytask)
        self.assertAlmostEquals(start,time.time(),places=1)

    def testStatusException(self):
        thread = self.thread_manager.do_async(exceptiontask)
        self.assertTrue(thread is not None)
        for x in [ 'CREATED', 'RUNNING', 'EXCEPTION' , 'FINISHING', 'CLOSED' ] :
            _,ec = thread.execution_state_queue.get()
            self.assertEqual(ec,x)
        self.assertEqual( thread.finished_with, 'EXCEPTION')
        self.assertEqual( thread.result.__class__, Exception)
        self.assertEqual( str(thread.result), '444')

    def testStatusSuccess(self):
        thread = self.thread_manager.do_async(notthingtask)
        self.assertTrue(thread is not None)
        for x in [ 'CREATED', 'RUNNING', 'RETURNED', 'FINISHING', 'CLOSED' ] :
            _,ec = thread.execution_state_queue.get()
            self.assertEqual(ec,x)
        self.assertEqual( thread.finished_with, 'RETURNED')
        self.assertEqual( thread.result.__class__, int)
        self.assertEqual( thread.result, 555)

    def testCallbackSucess(self):
        results=[]
        self.thread_manager.do_async(notthingtask,
                on_failure=lambda ex:results.append(str('ex')),
                on_end=lambda x:results.append(1),
                on_success=lambda x:results.append(x)).join()
        self.assertEqual(len(results),2)
        self.assertEqual(results[0],555)
        self.assertEqual(results[1],1)
    def testCallbackException(self):
        results=[]
        self.thread_manager.do_async(exceptiontask,
                on_failure=lambda ex:results.append(str(ex)),
                on_end=lambda x:results.append(1),
                on_success=lambda x:results.append(x)).join()
        self.assertEqual(len(results),2)
        self.assertEqual(results[0],'444')
        self.assertEqual(results[1],1)
    def testChildren(self):
        thread=self.thread_manager.do_async(sleepytask)
        keys = self.thread_manager.keys()
        self.assertEqual(len(keys),1)
        self.assertEqual(thread.ident,keys[0])
        self.assertTrue(thread is self.thread_manager[thread.ident])

class TestBackgroundTasker(unittest.TestCase):
    def tearDown(self):
        self.thread_manager.stop()
    def setUp(self):
        self.thread_manager = ThreadManager()
        self.bgtasker = BackgroundDecorator(self.thread_manager)
        self.thread_manager.start()

    def testAsync(self):
        @self.bgtasker
        def mpm():
            time.sleep(2)

        start= time.time()
        mpm()
        self.assertAlmostEquals(time.time(),start,places=2)

if __name__ == '__main__':
    unittest.main()
