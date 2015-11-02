##!/usr/bin/env python
## -*- coding: utf-8 -*-
#
#"""
#Test Script Application
#-------------------------
#"""
#
#import BAC0
#
#import unittest
#
#
#class TestReadWriteScript(unittest.TestCase):
#    """
#    Simple test to create a script start it and stop it.
#    """
#
#    def setUp(self):
#        """
#        Setup Test, should start script
#        """
#        self.bacnet = BAC0.ReadWriteScript()
#        
#    def test_bacnet_started(self):
#        assert self.bacnet._started == True
#
#    def test_bacnet_network_stop(self):
#        """
#        Stop it
#        """
#        self.bacnet.stopApp()
#        assert self.bacnet._started == False