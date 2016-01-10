#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Device
-------------------------
"""

from BAC0.core.io.Read import ReadProperty
from BAC0.core.app.ScriptApplication import ScriptApplication
from BAC0.core.io.IOExceptions import BokehServerCantStart, ReadPropertyException, ReadPropertyMultipleException, NoResponseFromController
from BAC0.core.devices.Device import Device
from BAC0.core.devices.Points import NumericPoint, BooleanPoint, EnumPoint
from BAC0.scripts import ReadWriteScript
from BAC0.bokeh.BokehServer import BokehServer
from BAC0.bokeh.BokehRenderer import BokehSession, BokehDocument

from mock import Mock, patch, call
import unittest
from threading import Event, Lock
from queue import Empty
import random
import pandas as pd
import logging
import time
import requests

from bacpypes.app import BIPSimpleApplication
from bacpypes.pdu import Address
from bacpypes.object import get_object_class, get_datatype
from bacpypes.apdu import PropertyReference, ReadAccessSpecification, \
    ReadPropertyMultipleRequest
from bacpypes.basetypes import PropertyIdentifier

class TestReadWriteScript(object):
    def __init__(self):
        self.bokehserver = False
        #self.start_bokeh()
    def start_bokeh(self):
        try:
            logging.getLogger("requests").setLevel(logging.INFO)
            self.BokehServer = BokehServer()
            self.BokehServer.start()
            self.bokeh_document = BokehDocument(title = 'BAC0 - Live Trending')
            self.new_bokeh_session()
            self.bokeh_session.loop()
            attemptedConnections = 0
            while requests.get('http://localhost:5006').status_code != 200:
                time.sleep(0.1)
                attemptedConnections += 1
                if attemptedConnections > 10:
                    raise BokehServerCantStart
            self.bokehserver = True
        except OSError as error:
            self.bokehserver = False
            print('Please start bokeh serve to use trending features')
            print('controller.chart will not work')
        except RuntimeError as rterror:
            self.bokehserver = False
            print('Server already running')
        except BokehServerCantStart:
            self.bokehserver = False
            print("Can't start Bokeh Server")
            print('controller.chart will not work')

    def new_bokeh_session(self):
        self.bokeh_session = BokehSession(self.bokeh_document.document)


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
        self.ResponseQueue.get.return_value = ([21, 'degreesCelcius'], Event())
        self.request = Mock()
        self.value = None

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
        network = TestReadWriteScript()
        self.fake_device = FakeDevice('2:5', 842, network)
          
    def test_av1_between_0_100(self):
        """
        TestDevice / Reading av1 should return a value between 0 and 100
        """
        self.assertTrue(0 <= self.fake_device['av1'] <= 100)
        
    def test_bv1_true_or_false(self):
        """
        TestDevice / Reading bv1 should return 'inactive' or 'active'..._boolkey must be bool
        """
        self.assertTrue(self.fake_device['bv1'].value in ['inactive','active'])
        self.assertTrue(isinstance(self.fake_device['bv1']._boolKey, bool))

    def test_av1_is_number(self):
        """
        TestDevice / av1 should always be a number
        """
        self.assertTrue(isinstance(self.fake_device['av1'].value, float))

    def test_histories(self):
        """
        TestDevice / Histories must be pandas Series
        """
        self.assertTrue(isinstance(self.fake_device['av1'].history, pd.Series))
        self.assertTrue(isinstance(self.fake_device['bv1'].history, pd.Series))
        self.assertTrue(isinstance(self.fake_device['mv1'].history, pd.Series))

    def test_dataframe_from_list_of_points(self):
        """
        TestDevice / df function must return a pandas DataFrame provided a list
        """
        df = self.fake_device.df(['av1','bv1','mv1'])
        self.assertTrue(isinstance(df, pd.DataFrame))
        self.assertTrue('av1' in df.columns)
        self.assertTrue('bv1' in df.columns)
        self.assertTrue('mv1' in df.columns)
        self.assertFalse('av2' in df.columns)

#    def test_chart_from_list_of_points(self):
#        """
#        TestDevice / Build a chart
#        """        
#        self.fake_device.chart(['av1','bv1','mv1'])
