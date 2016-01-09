#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Device
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
import random
import pandas as pd

from BAC0.core.io.IOExceptions import ReadPropertyException, ReadPropertyMultipleException, NoResponseFromController
from BAC0.core.devices.Device import Device
from BAC0.core.devices.Points import NumericPoint, BooleanPoint, EnumPoint


class TestNumericPoint(NumericPoint):
    @property
    def value(self):
        return random.uniform(0, 100)

class TestBooleanPoint(BooleanPoint):
    @property
    def value(self):
        res = random.choice(['inactive', 'active'])
        self._trend(res)
        if res == 'inactive':
            self._key = 0
            self._boolKey = False
        else:
            self._key = 1
            self._boolKey = True
        return res

class TestEnumPoint(EnumPoint):
    @property
    def value(self):
        return random.randint(1,3)

class FakeDevice(Device):
    """
    Let's begin with a fake device
    """
    #@patch('BAC0.core.devices.Points.Point.value')
    #@patch('BAC0.core.devices.Device.Device._buildPointList'                               
            
    def _buildPointList(self):
        self.properties.objects_list = [('analogValue', 1),
                                    ('multistateValue', 1),
                                    ('binaryValue', 1)]
                                    
        av1 = TestNumericPoint(
                    pointType='analogValue',
                    pointAddress=1,
                    pointName='av1',
                    description='test_av1',
                    presentValue=10,
                    units_state='percent',
                    device=self)
        mv1 = TestEnumPoint(
                    pointType='multistateValue',
                    pointAddress=1,
                    pointName='mv1',
                    description='test_mv1',
                    presentValue=1,
                    units_state=['Off','On','Auto'],
                    device=self)
                    
        bv1 = TestBooleanPoint(
                    pointType='binaryValue',
                    pointAddress=1,
                    pointName='bv1',
                    description='test_bv1',
                    presentValue='inactive',
                    units_state=('off', 'on'),
                    device=self)
        
        test_points = [av1,mv1,bv1]
        for point in test_points:
            self.points.append(point)
    def read_multiple(self, points_list, *, points_per_request=25, discover_request=(None, 6)):
        for point in self.points:
            point.value
            print(point)

class TestDevice(unittest.TestCase):
    def setUp(self):
        self.fake_device = FakeDevice('2:5', 842, None)
          
    def test_av1_between_0_100(self):
        self.assertTrue(0 <= self.fake_device['av1'] <= 100)
        
    def test_bv1_true_or_false(self):
        self.assertTrue(self.fake_device['bv1'].value in ['inactive','active'])
        self.assertTrue(isinstance(self.fake_device['bv1']._boolKey, bool))
        print(type(self.fake_device['bv1'].value))

    def test_av1_is_number(self):
        self.assertTrue(isinstance(self.fake_device['av1'].value, float))

    def test_histories(self):
        self.assertTrue(isinstance(self.fake_device['av1'].history, pd.Series))
        self.assertTrue(isinstance(self.fake_device['bv1'].history, pd.Series))
        self.assertTrue(isinstance(self.fake_device['mv1'].history, pd.Series))

    def test_dataframe_from_list_of_points(self):
        self.assertTrue(isinstance(self.fake_device.df(['av1','bv1','mv1']), pd.DataFrame))

    def test_chart_from_list_of_points(self):
        self.fake_device.chart(['av1','bv1','mv1'])

#class TestReadPropertyClass(ReadProperty):
#    """
#    This class replaces the __init__ method for testing purposes.
#    This way, we can mock the behaviour.
#    """
#
#    def __init__(self):
#        self.this_application = TestScriptApplication()
#        self.this_application._lock = Lock()
#
#
#class TestBokehRendering(unittest.TestCase):
#    """
#    Test with mock
#    """
#    @patch('BAC0.core.devices.Device.Device')
#    def setUp(self, mock_device):
#        pass

