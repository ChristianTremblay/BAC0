#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Simulation
-------------------------
"""

from BAC0.core.io.Simulate import Simulation
from BAC0.core.app.ScriptApplication import ScriptApplication
from BAC0.core.io.IOExceptions import OutOfServiceNotSet, OutOfServiceSet

from mock import Mock, patch, call
import unittest

from bacpypes.app import BIPSimpleApplication
from bacpypes.pdu import Address
from bacpypes.object import get_object_class, get_datatype
from bacpypes.apdu import PropertyReference, ReadAccessSpecification, \
    ReadPropertyMultipleRequest
from bacpypes.basetypes import PropertyIdentifier

from threading import Event
from queue import Empty


class TestScriptApplication(ScriptApplication):
    """
    This class replaces the __init__ method for testing purposes.
    This way, we can mock the behaviour.
    """
    @patch('bacpypes.app.BIPSimpleApplication.__init__')
    def __init__(self, *args):
        BIPSimpleApplication.__init__(Mock())
        self.elementService = Mock()
        self.ResponseQueue = Mock()
#        self.ResponseQueue.get.return_value = ('inactive', Event())
        self.request = Mock()
        self.value = None


class TestSimulateClass(Simulation):
    """
    This class replaces the __init__ method for testing purposes.
    This way, we can mock the behaviour.
    """

    def __init__(self):
        self.this_application = TestScriptApplication()
        self.simulatedPoints = []
        self.read = Mock()
        self.write = Mock()


class TestSimulate(unittest.TestCase):
    """
    Test with mock
    """
    @patch('BAC0.core.io.Read.ReadProperty.read')
    @patch('BAC0.core.app.ScriptApplication.ScriptApplication.__init__')
    @patch('bacpypes.app.BIPSimpleApplication.__init__')
    def setUp(self, mock_BIPSimpleApplication, mock_ScriptApplication, mock_read):
        self.req = '2:5 analogValue 1 presentValue 100'
        mock_ScriptApplication.return_value = TestScriptApplication()
        mock_BIPSimpleApplication.return_value = None
        self.simulation = TestSimulateClass()
        self.simulation._started = True

    def test_read_outOfService_prop_request_is_correct(self):
        """
        Simulation / Request used for method call should be equivalent to base_request
        """
        self.simulation.sim(self.req)
        self.simulation.read.return_value = True
        assert self.simulation.read.called
        self.arg_used_in_call = (
            self.simulation.read.call_args)[0][0]
        self.base_request = call('2:5 analogValue 1 outOfService')[1][0]

        self.assertEqual(
            self.arg_used_in_call,
            self.base_request)

    def test_not_started_sim(self):
        """
        Simulation / If application not started, raise Exception
        """
        self.req = '2:5 analogValue 1 presentValue 100'
        self.simulation._started = False
        with self.assertRaises(Exception):
            self.simulation.sim(self.req)
            
    def test_not_started_release(self):
        """
        Simulation / If application not started, raise Exception
        """
        self.req = '2:5 analogValue 1'
        self.simulation._started = False
        with self.assertRaises(Exception):
            self.simulation.release(self.req)

    def test_outOfServiceNotSetException(self):
        """
        Simulation / test_outOfServiceNotSetException
        """
        self.req = '2:5 analogValue 1 presentValue 100'
        self.simulation.read.return_value = False
        with self.assertRaises(OutOfServiceNotSet):
            self.simulation.sim(self.req)

    def test_write_prop_request_is_correct(self):
        """
        Simulation / Request used for write call should be equivalent to base_request
        Beware : harde to test how write handles the 2 calls when outOfService is False... 
        It raises the exception and I can't seem to be able to test inside the with context 
        manager.        
        """        
        self.simulation.read.return_value = True           
        self.simulation.sim(self.req)
        self.assertEqual(self.simulation.write.call_count, 1)
        
    def test_release_request(self):
        """
        Simulation / Releae request used for method call should be equivalent to base_request
        """
        self.req = '2:5 analogValue 1'
        self.simulation.read.return_value = False
        self.simulation.release(self.req)
        assert self.simulation.write.called
        self.arg_used_in_call = (
            self.simulation.write.call_args)[0][0]
        self.base_request = call('2:5 analogValue 1 outOfService False')[1][0]

        self.assertEqual(
            self.arg_used_in_call,
            self.base_request)       

    def test_outOfServiceSetException(self):
        """
        Simulation / test_outOfServiceNotSetException
        """
        self.req = '2:5 analogValue 1'
        self.simulation.read.return_value = True
        with self.assertRaises(OutOfServiceSet):
            self.simulation.release(self.req)