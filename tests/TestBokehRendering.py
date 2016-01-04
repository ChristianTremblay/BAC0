#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Read Property
-------------------------
"""

from BAC0.core.io.Read import ReadProperty
from BAC0.core.app.ScriptApplication import ScriptApplication

from mock import Mock, patch, call
import unittest

from bacpypes.app import BIPSimpleApplication
from bacpypes.pdu import Address
from bacpypes.object import get_object_class, get_datatype
from bacpypes.apdu import PropertyReference, ReadAccessSpecification, \
    ReadPropertyMultipleRequest
from bacpypes.basetypes import PropertyIdentifier

from threading import Event, Lock
from queue import Empty

from BAC0.core.io.IOExceptions import ReadPropertyException, ReadPropertyMultipleException, NoResponseFromController
from BAC0.core.devices.Device import Device


class TestDevice(Device):
    """
    Let's begin with a fake device
    """
    @patch('BAC0.core.devices.Device.Device._buildPointList')
    def __init__(self, address, device_id, network, *, poll=10):
        self.properties.pss.value = [1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 
                                     1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0,
                                     0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 
                                     1, 0, 1, 0, 0, 1]
        self.properties.name = 'FakeDevice'                             
        self._buildPointList.get.return_value = None
        self.properties.objects_list = [('file', 1),
                                        ('analogInput', 2),
                                        ('analogInput', 3)]
        self.points = [nvoAI3 : 2.58 degreesCelsius,
                       nvoAI4 : 45.34 percent,
        self.request = Mock()
        self.value = None


class TestReadPropertyClass(ReadProperty):
    """
    This class replaces the __init__ method for testing purposes.
    This way, we can mock the behaviour.
    """

    def __init__(self):
        self.this_application = TestScriptApplication()
        self.this_application._lock = Lock()


class TestBokehRendering(unittest.TestCase):
    """
    Test with mock
    """
    @patch('BAC0.core.devices.Device.Device')
    def setUp(self, mock_device):
        pass

