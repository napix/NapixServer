#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2

from mock.default_managers import MockReadOnlyDictManager,MockDictManager,MockListManager

from napixd.exceptions import NotFound,Duplicate

class TestReadOnlyDict(unittest2.TestCase):
    def setUp(self):
        self.manager = MockReadOnlyDictManager({})
    def testGET(self):
        self.assertListEqual(sorted(self.manager.list_resource()),['one','three','two'])
        self.assertDictEqual(self.manager.get_resource('one'),{'french':'un','german':'eins'})

class TestDictManager(unittest2.TestCase):
    def setUp(self):
        self.manager = MockDictManager({})

    def testGET(self):
        self.assertListEqual(sorted(self.manager.list_resource()),['one','three','two'])
        self.assertDictEqual(self.manager.get_resource('one'),
                {'english':'one','french':'un','german':'eins'})

    def testDELETE(self):
        self.manager.delete_resource('one')
        self.assertRaises(NotFound,self.manager.get_resource,'one')
        self.assertDictEqual(self.manager.resources, {
            'two':{'french':'deux','german':'zwei','english':'two'},
            'three':{'french':'trois','german':'drei','english':'three'}
            })
    def testPUT(self):
        self.manager.modify_resource('one',{'english':'one','french':'une','german':'eins'})
        self.assertDictEqual(self.manager.get_resource('one'),
                {'english':'one','french':'une','german':'eins'})
        self.assertDictEqual(self.manager.resources, {
            'one':{'english':'one','french':'une','german':'eins'},
            'two':{'french':'deux','german':'zwei','english':'two'},
            'three':{'french':'trois','german':'drei','english':'three'}
            })

    def testPOST(self):
        self.assertRaises(Duplicate, self.manager.create_resource,
                {'english':'one','french':'une','german':'eins'})
        self.assertEqual(self.manager.create_resource(
            {'english':'four','french':'quatre','german':'vier'}),'four')
        self.assertDictEqual(self.manager.get_resource('four'),
                {'english':'four','french':'quatre','german':'vier'})
        self.assertDictEqual(self.manager.resources, {
            'one':{'english':'one','french':'un','german':'eins'},
            'two':{'french':'deux','german':'zwei','english':'two'},
            'three':{'french':'trois','german':'drei','english':'three'},
            'four':{'french':'quatre','german':'vier','english':'four'}
            })

class TestListManager(unittest2.TestCase):
    def setUp(self):
        self.manager = MockListManager({})

    def testGET(self):
        self.assertListEqual(self.manager.list_resource(),[0,1,2])
        self.assertDictEqual(self.manager.get_resource(0),
                {'english':'one','french':'un','german':'eins'})
    def testPUT(self):
        self.manager.modify_resource(0,{'english':'one','french':'une','german':'eins'})
        self.assertDictEqual(self.manager.get_resource(0),
                {'english':'one','french':'une','german':'eins'})
        self.assertListEqual(self.manager.resources, [
            {'english':'one','french':'une','german':'eins'},
            {'french':'deux','german':'zwei','english':'two'},
            {'french':'trois','german':'drei','english':'three'}
            ])
    def testPOST(self):
        self.assertEqual(self.manager.create_resource(
            {'english':'four','french':'quatre','german':'vier'}),3)
        self.assertDictEqual(self.manager.get_resource(3),
                {'english':'four','french':'quatre','german':'vier'})
        self.assertListEqual(self.manager.resources, [
            {'english':'one','french':'un','german':'eins'},
            {'french':'deux','german':'zwei','english':'two'},
            {'french':'trois','german':'drei','english':'three'},
            {'french':'quatre','german':'vier','english':'four'}
            ])


if __name__ == '__main__':
    unittest2.main()
