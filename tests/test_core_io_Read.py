#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Script Application
-------------------------
"""

from BAC0.scripts.ReadWriteScript import ReadWriteScript
from BAC0.core.functions.GetIPAddr import HostIP

import unittest
import mock

class Test_Scripts_ReadWriteScript_mock(unittest.TestCase):

#    mock.patch('BAC0.bacpypes')
#    def test_creation_of_script_autoIP(self, mock_bacpypes): 
#        mock_readwritescript = unittest.mock.create_autospec(ReadWriteScript)
#        bacnet = ReadWriteScript(mock_readwritescript)
#        
#        # Test that whois is created
#        bacnet.whois.assert_called()
#        bacnet.stopApp()
#        
#    def test_creation_of_script_givenIP(self, mock_bacpypes): 
##        mock_readwritescript = unittest.mock.create_autospec(ReadWriteScript)
#        ip = HostIP()
#        bacnet = ReadWriteScript(localIPAddr = ip.getIPAddr())
#        
#        # Test that whois is created
# #       bacnet.whois.assert_called()
#        bacnet.stopApp()     
    def test_nothing(self):
        pass