#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sys
import unittest2
from threading import Thread,current_thread,Event

from napixd.executor import Executor

ready = Event()


class ExecutorProxy(object):
    def __init__(self):
        self.renew()
    def renew(self):
        self.executor = Executor()

    def __getattr__(self,at):
        return getattr(self.executor,at)

executor = ExecutorProxy()

@unittest2.skipIf(__name__ != '__main__', 'This test must be launched directly')
class TestExecutor(unittest2.TestCase):
    def tearDown(self):
        ready.clear()
        executor.stop()
        executor.renew()
    def setUp(self):
        ready.set()

    def testRequest(self):
        process = executor.create_job(['/bin/echo','what up','dude'],discard_output=False)
        self.assertEqual(process.request.command,'/bin/echo')
        self.assertEqual(process.request.commandline,'/bin/echo "what up" dude')
        expected = ['what up','dude']
        actual = process.request.arguments
        self.assertEqual(len(actual),len(expected))
        for args in zip(actual,expected):
            self.assertEqual(*args)
        process.wait()
        self.assertEqual(process.stdout.read(),'what up dude\n')
        self.assertEqual(process.stderr.read(),'')
        self.assertEqual(process.returncode,0)
    def testOSError(self):
        self.assertRaises(OSError,
            executor.create_job,['something_that_does_not_exist'])
    def testFalse(self):
        process = executor.create_job(['/bin/false'])
        process.wait()
        self.assertEqual(process.returncode,1)
    def testKill(self):
        process = executor.create_job('yes',discard_output=True)
        process.kill()
        self.assertEqual(process.returncode,-15)
    def testOwner(self):
        process = executor.create_job(['sleep','3'])
        time.sleep(0.1)
        children = executor.children_of(current_thread().ident)
        self.assertEqual(len(children),1)
        self.assertEqual(process,children[0])
        process.kill()
        time.sleep(0.1)
        children = executor.children_of(current_thread().ident)
        self.assertEqual(children,[])


def main():
    unittest2.main()

if __name__ == '__main__':
    t=Thread(target=main).start()
    while ready.wait(1) or ready.is_set():
        executor.run()
