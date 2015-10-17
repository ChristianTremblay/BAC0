#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Script Application
-------------------------
"""

import BAC0

import unittest

class Test_Scripts_ReadWriteScript(unittest.TestCase):
    def setUp(self):
        self.bacnet = BAC0.ReadWriteScript()        
        
    def test_bacnet_network_stop(self):
        self.bacnet.stopApp()