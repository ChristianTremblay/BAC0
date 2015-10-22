#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Script Application
-------------------------
"""

import BAC0
from BAC0.scripts.ReadWriteScript import ReadWriteScript
from BAC0.core.functions.GetIPAddr import HostIP

import unittest
from mock import Mock, patch

class Test_Scripts_ReadWriteScript_mock(unittest.TestCase):

    @patch('BAC0.core.app.ScriptApplication.ScriptApplication')
    def test_creation_of_script_autoIP(self, mock_ScriptApplication): 
        #mock_ScriptApplication = unittest.mock.create_autospec(ReadWriteScript)
        bacnet = BAC0.ReadWriteScript()
        
        # Test that whois is created
        bacnet.whois.assert_called()
        bacnet.stopApp()
        
#    def test_creation_of_script_givenIP(self, mock_bacpypes): 
#        mock_readwritescript = unittest.mock.create_autospec(ReadWriteScript)
#        ip = HostIP()
#        bacnet = ReadWriteScript(localIPAddr = ip.getIPAddr())
        
#        # Test that whois is created
#       bacnet.whois.assert_called()
#        bacnet.stopApp()     
