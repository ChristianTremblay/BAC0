#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.

"""
How to describe a bacnet device
"""
from bacpypes.basetypes import ServicesSupported

from .Points import NumericPoint, BooleanPoint, EnumPoint, OfflinePoint
from ..io.IOExceptions import NoResponseFromController, ReadPropertyMultipleException
from ...tasks.Poll import DevicePoll
from ...bokeh.BokehRenderer import BokehPlot
from ...sql.sql import SQLMixin
#from .states.DeviceDisconnected import DeviceDisconnected
from .mixins.read_property_multiple import Read

from collections import namedtuple
import pandas as pd
from datetime import datetime

import sqlite3
import pandas as pd
from pandas.lib import Timestamp
from pandas.io import sql

try:
    from xlwings import Workbook, Sheet, Range, Chart
    _XLWINGS = True
except ImportError:
    print('xlwings not installed. If using Windows or OSX, install to get more features.')
    _XLWINGS = False
    
# Credit : Raymond Hettinger
def fix_docs(cls):
    for name, func in vars(cls).items():
        if not func.__doc__:
            #print(func, 'needs doc')
            for parent in cls.__bases__:
                parfunc = getattr(parent, name)
                if parfunc and getattr(parfunc, '__doc__', None):
                    #func.__doc__ = parfunc.__doc__
                    break
    return cls
    
class DeviceProperties(object):
    """
    This serves as a container for device properties
    """
    def __init__(self):
        self.name = None
        self.address = None
        self.device_id = None
        self.network = None
        self.pollDelay = None
        self.objects_list = None
        self.pss = ServicesSupported()
        self.serving_chart = None
        self.charts = None
        self.multistates = None
        self.db = None

    @property
    def asdict(self):
        return self.__dict__

class Device(SQLMixin, Read):
    """
    Bacnet device
    This class represents a controller. When defined, it allows
    the use of read, write, sim, release functions to communicate
    with the device on the network
    """

    def __init__(self, address, device_id, network, *, poll=10):
        """
        Initialization require address, device id and bacnetApp (the script itself)
        :param addr: address of the device (ex. '2:5')
        :param device_id: bacnet device ID (boid)
        :param network: defined by BAC0.connect()
        :param poll: (int) if > 0, will poll every points each x seconds.
        :type address: (str)
        :type device_id: int
        :type network: BAC0.scripts.ReadWriteScript.ReadWriteScript
        """
        self.properties = DeviceProperties()

        self.properties.address = address
        self.properties.device_id = device_id
        self.properties.network = network
        self.properties.pollDelay = poll
        self.properties.name = ''
        self.properties.objects_list = []
        self.properties.pss = ServicesSupported()
        self.properties.serving_chart = {}
        self.properties.charts = []
        self.properties.multistates = {}
        # Todo : find a way to normalize the name of the db
        self.properties.db = 'controller.db'

        self.points = []

        self._polling_task = namedtuple('_polling_task', ['task', 'running'])
        self._polling_task.task = None
        self._polling_task.running = False

        self._notes = namedtuple('_notes',
                                   ['timestamp', 'notes'])

        self._notes.timestamp = []
        self._notes.notes = []
        self._notes.notes.append("Controller initialized")
        self._notes.timestamp.append(datetime.now())

        print('Calling new state : disconnected')
        self.new_state(DeviceDisconnected)
        self.connect_to_device_or_db()
        
    def new_state(self, newstate):
        self.__class__ = newstate
        
    def connect_to_device_or_db(self):
        raise NotImplementedError()

    def connect_to_db(self):
        raise NotImplementedError() 

    def initialize_device_from_db(self):
        raise NotImplementedError()

    @property
    def notes(self):
        """
        Notes allow the user to add text notes to the device.
        Notes are stored as timeseries (same than points)
        :returns: pd.Series
        """
        notes_table = pd.Series(self._notes.notes,
                              index=self._notes.timestamp)
        return notes_table
        
    @notes.setter
    def notes(self,note):
        """
        Setter for notes
        :param note: (str)
        """
        self._notes.timestamp.append(datetime.now())
        self._notes.notes.append(note)
        
    def df(self, list_of_points, force_read = True):
        """
        df is a way to build a pandas DataFrame from a list of points
        DataFrame can be used to present data or analysis
        
        :param list_of_points: a list of point names as str
        :returns: pd.DataFrame
        """
        raise NotImplementedError()
        
    def chart(self, list_of_points, *, title = 'Live Trending', show_notes = True):
        """
        chart offers a way to draw a chart from a list of points.
        It allows to pass args to the pandas plot() functions
        refer to the pandas and matplotlib doc for details.
        :param list_of_points: a list of point name as str
        :param plot_args: arg for plot function
        :returns: plot()
        """
        if self.__class__ == DeviceFromDB:
            update_data = False
        else:
            update_data = True
        if self.properties.network.bokehserver:
            lst = []
            for point in list_of_points:
                if point in self.points_name:
                    #print('Add %s to list' % point)
                    lst.append(point)
                else:
                    print('Wrong name, removing %s from list' % point)
            try:                    
                self.properties.serving_chart[title] = BokehPlot(self,lst, title = title, show_notes = show_notes, update_data = update_data)
            except Exception as error:
                print('A problem occurred : %s' % error)
        else:
            print("No bokeh server running, can't display chart")

            
    @property
    def simulated_points(self):
        """
        iterate over simulated points
        :returns: points if simulated (out_of_service == True)
        :rtype: BAC0.core.devices.Points.Point
        """
        for each in self.points:
            if each.properties.simulated:
                yield each

    def _buildPointList(self):
        """
        Read all points of the device and creates a dataframe (Pandas) to store
        the list and allow quick access.
        This list will be used to access variables based on point name
        """
        raise NotImplementedError()
        

    def __getitem__(self, point_name):
        """
        Get a point based on its name
        If a list is passed, will return a dataframe

        :param point_name: (str) name of the point or list of point_names
        :type point_name: str     
        :returns: (Point) the point (can be Numeric, Boolean or Enum) or pd.DataFrame
        """
        raise NotImplementedError()

    def __iter__(self):
        """
        When iterating a device, iterate points of it.
        """
        raise NotImplementedError()
            
    def __contains__(self, value):
        "When using in..."
        raise NotImplementedError()

    @property
    def points_name(self):
        """
        When iterating a device, iterate points of it.
        """
        raise NotImplementedError()
            
    def to_excel(self):
        """
        Using xlwings, make a dataframe of all histories and save it 
        """
        raise NotImplementedError()

    def __setitem__(self, point_name, value):
        """
        Write, sim or ovr value
        :param point_name: Name of the point to set
        :param value: value to write to the point
        :type point_name: str
        :type value: float
        """
        raise NotImplementedError()

    def __len__(self):
        """
        Will return number of points available
        """
        raise NotImplementedError()

    def _parseArgs(self, arg):
        """
        Given a string, will interpret the last word as the value, everything else
        will be considered the point name
        """
        args = arg.split()
        pointName = ' '.join(args[:-1])
        value = args[-1]
        return (pointName, value)

    @property
    def analog_units(self):
        raise NotImplementedError()

    @property
    def temperatures(self):
        raise NotImplementedError()

    @property
    def percent(self):
        raise NotImplementedError()
        
    @property
    def multi_states(self):
        raise NotImplementedError()
        
    @property
    def binary_states(self):
        raise NotImplementedError()

    def _discoverPoints(self):
        """
        This function allows the discovery of all bacnet points in a device

        :returns: (deviceName, pss, objList, df)
        :rtype: tuple

        *deviceName* : name of the device
        *pss* : protocole service supported
        *objList* : list of bacnet object (ex. analogInput, 1)
        *df* : is a dataFrame containing pointType, pointAddress, pointName, description
        presentValue and units

        If pandas can't be found, df will be a simple array

        """
        raise NotImplementedError()

    def _findPoint(self, name, force_read=True):
        """
        Helper that retrieve point based on its name.

        :param name: (str) name of the point
        :param force_read: (bool) read value of the point each time the func
                            is called.
        :returns: Point object
        :rtype: BAC0.core.devices.Point.Point (NumericPoint, EnumPoint or
        BooleanPoint)

        """
        raise NotImplementedError()

    def __repr__(self):
        return '%s / Undefined' % self.properties.name

@fix_docs
class DeviceConnected(Device):
    def connect_to_db(self):
        print('Connect to db not implemented')
        pass

    def connect_to_device_or_db(self):
        print('Already connected')        


    def df(self, list_of_points, force_read = True):
        his = []
        for point in list_of_points:
            try:
                his.append(self._findPoint(point, force_read = force_read).history)
            except ValueError as ve:
                print('%s' % ve)                
                continue
    
        return pd.DataFrame(dict(zip(list_of_points,his)))
        
    def _buildPointList(self):
        try:
            self.properties.pss.value = self.properties.network.read(
                '%s device %s protocolServicesSupported' %
                (self.properties.address, self.properties.device_id))
        except NoResponseFromController as error:
            print('Controller not found, aborting. (%s)' % error)
            return ('Not Found', '', [], [])
        self.properties.name = self.properties.network.read(
            '%s device %s objectName' %
            (self.properties.address, self.properties.device_id))
        print('Found %s... building points list' % self.properties.name)
        self.properties.objects_list, self.points = self._discoverPoints()


    def __getitem__(self, point_name):
        try:
            if isinstance(point_name,list):
                return self.df(point_name, force_read = False)
            else:
                return self._findPoint(point_name)
        except ValueError as ve:
            print('%s' % ve)

    def __iter__(self):
        for each in self.points:
            yield each
            
    def __contains__(self, value):
        return value in self.points_name

    @property
    def points_name(self):
        for each in self.points:
            yield each.properties.name
            
    def to_excel(self):
        his = {}
        for name in list(self.points_name):
            try:
                his[name] = self._findPoint(name, force_read=False).history.replace(['inactive', 'active'], [0, 1]).resample('1ms')
            except TypeError:
                his[name] = self._findPoint(name, force_read=False).history.resample('1ms')
        
        his['Notes'] = self.notes
        df = pd.DataFrame(his).fillna(method='ffill').fillna(method='bfill')

        if _XLWINGS:        
            wb = Workbook()
            Range('A1').value = df
        else:
            df.to_csv()

    def __setitem__(self, point_name, value):
        try:
            self._findPoint(point_name)._set(value)
        except ValueError as ve:
            print('%s' % ve)

    def __len__(self):
        return len(self.points)

    def _parseArgs(self, arg):
        args = arg.split()
        pointName = ' '.join(args[:-1])
        value = args[-1]
        return (pointName, value)

    @property
    def analog_units(self):
        au = []
        us = []
        for each in self.points:
            if isinstance(each, NumericPoint):
                au.append(each.properties.name)
                us.append(each.properties.units_state)
        return dict(zip(au,us))

    @property
    def temperatures(self):
        for each in self.analog_units.items():
            if "deg" in each[1]:
                yield each

    @property
    def percent(self):
        for each in self.analog_units.items():
            if "percent" in each[1]:
                yield each
        
    @property
    def multi_states(self):
        ms = []
        us = []
        for each in self.points:
            if isinstance(each, EnumPoint):
                ms.append(each.properties.name)
                us.append(each.properties.units_state)
        return dict(zip(ms,us))
        
    @property
    def binary_states(self):
        bs = []
        us = []
        for each in self.points:
            if isinstance(each, BooleanPoint):
                bs.append(each.properties.name)
                us.append(each.properties.units_state)
        return dict(zip(bs,us))

    def _discoverPoints(self):
        objList = self.properties.network.read(
            '%s device %s objectList' %
            (self.properties.address, self.properties.device_id))

        points = []

        def retrieve_type(obj_list, point_type_key):
            """
            retrive analog values
            """
            for point_type, point_address in obj_list:
                if point_type_key in point_type:
                    yield (point_type, point_address)

        # Numeric
        analog_request = []
        list_of_analog = retrieve_type(objList, 'analog')
        for analog_points, address in list_of_analog:
            analog_request.append('%s %s objectName presentValue units description ' %
                                  (analog_points, address))
        analog_points_info = self.read_multiple(
            '', discover_request=(analog_request, 4), points_per_request=5)
        i = 0
        for each in retrieve_type(objList, 'analog'):
            point_type = str(each[0])
            point_address = str(each[1])
            point_infos = analog_points_info[i]
            i += 1
            points.append(
                NumericPoint(
                    pointType=point_type,
                    pointAddress=point_address,
                    pointName=point_infos[0],
                    description=point_infos[3],
                    presentValue=float(point_infos[1]),
                    units_state=point_infos[2],
                    device=self))

        multistate_request = []
        list_of_multistate = retrieve_type(objList, 'multi')
        for multistate_points, address in list_of_multistate:
            multistate_request.append('%s %s objectName presentValue stateText description ' %
                                      (multistate_points, address))

        multistate_points_info = self.read_multiple(
            '', discover_request=(multistate_request, 4), points_per_request=5)

        i = 0
        for each in retrieve_type(objList, 'multi'):
            point_type = str(each[0])
            point_address = str(each[1])
            point_infos = multistate_points_info[i]
            i += 1
            points.append(
                EnumPoint(
                    pointType=point_type,
                    pointAddress=point_address,
                    pointName=point_infos[0],
                    description=point_infos[3],
                    presentValue=point_infos[1],
                    units_state=point_infos[2],
                    device=self))

        binary_request = []
        list_of_binary = retrieve_type(objList, 'binary')
        for binary_points, address in list_of_binary:
            binary_request.append('%s %s objectName presentValue inactiveText activeText description ' %
                                  (binary_points, address))

        binary_points_info = self.read_multiple(
            '', discover_request=(binary_request, 5), points_per_request=5)

        i = 0
        for each in retrieve_type(objList, 'binary'):
            point_type = str(each[0])
            point_address = str(each[1])
            point_infos = binary_points_info[i]
            i += 1
            points.append(
                BooleanPoint(
                    pointType=point_type,
                    pointAddress=point_address,
                    pointName=point_infos[0],
                    description=point_infos[4],
                    presentValue=point_infos[1],
                    units_state=(point_infos[2], point_infos[3]),
                    device=self))
        print('Ready!')
        return (objList, points)

    def _findPoint(self, name, force_read=True):
        for point in self.points:
            if point.properties.name == name:
                if force_read:
                    point.value
                return point
        raise ValueError("%s doesn't exist in controller" % name)

    def __repr__(self):
        return '%s / Connected' % self.properties.name

@fix_docs
class DeviceDisconnected(Device):
    def connect_to_device_or_db(self):        
        try:
            ojbect_list = self.properties.network.read(
            '%s device %s objectList' %
            (self.properties.address, self.properties.device_id))
            if ojbect_list:
                print('Calling new state : DeviceConnected')
                self.new_state(DeviceConnected)
                self._buildPointList()
                if self.properties.pollDelay > 0:
                    self.poll()
        except NoResponseFromController:
            print('Calling new state : DeviceFromDB')
                
            self.new_state(DeviceFromDB)
            self.initialize_device_from_db()
            
        
    def df(self, list_of_points, force_read = True):
        raise DeviceNotConnected('Must connect to bacnet or database') 
        
    @property
    def simulated_points(self):
        for each in self.points:
            if each.properties.simulated:
                yield each

    def _buildPointList(self):
        raise DeviceNotConnected('Must connect to bacnet or database') 




# This should be a "read" function and rpm defined in state rpm
    def read_multiple(self, points_list, *, points_per_request=25, discover_request=(None, 6)):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    def poll(self, command='start', *, delay=10):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    def __getitem__(self, point_name):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    def __iter__(self):
        raise DeviceNotConnected('Must connect to bacnet or database') 
            
    def __contains__(self, value):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    @property
    def points_name(self):
        raise DeviceNotConnected('Must connect to bacnet or database') 
            
    def to_excel(self):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    def __setitem__(self, point_name, value):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    def __len__(self):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    @property
    def analog_units(self):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    @property
    def temperatures(self):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    @property
    def percent(self):
        raise DeviceNotConnected('Must connect to bacnet or database') 
        
    @property
    def multi_states(self):
        raise DeviceNotConnected('Must connect to bacnet or database') 
        
    @property
    def binary_states(self):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    def _discoverPoints(self):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    def _findPoint(self, name, force_read=True):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    def __repr__(self):
        return '%s / Disconnected' % self.properties.name

@fix_docs
class DeviceFromDB(DeviceConnected):
    def connect_to_device_or_db(self):        
        try:
            ojbect_list = self.properties.network.read(
            '%s device %s objectList' %
            (self.properties.address, self.properties.device_id))
            if ojbect_list:
                print('Calling new state : DeviceConnected(SQLMixin, Read)')
                self.new_state(DeviceConnected)
                self.db.close()
                self.db = None
                self._buildPointList()
                if self.properties.pollDelay > 0:
                    self.poll()
        except NoResponseFromController:
            print('Unable to connect, keeping DB mode active')

    def initialize_device_from_db(self):
        print('Initializing DB')
        self.db = sqlite3.connect(self.properties.db)
        self.points = []
        for point in self.points_from_sql(self.db):
            self.points.append(OfflinePoint(self,point))
        self.properties = DeviceProperties()
        self.properties.address = self.dev_prop('FX14 0005')['address']
        self.properties.device_id = self.dev_prop('FX14 0005')['device_id']
        self.properties.network = 'Offline'
        self.properties.pollDelay = self.dev_prop('FX14 0005')['pollDelay']
        self.properties.name = self.dev_prop('FX14 0005')['name']
        self.properties.objects_list = self.dev_prop('FX14 0005')['objects_list']
        self.properties.pss = ServicesSupported()
        self.properties.serving_chart = {}
        self.properties.charts = []
        self.properties.multistates = self.dev_prop('FX14 0005')['multistates']
                
    @property
    def simulated_points(self):
        for each in self.points:
            if each.properties.simulated:
                yield each

    def _buildPointList(self):
        raise DeviceNotConnected('Must connect to bacnet or database') 

# This should be a "read" function and rpm defined in state rpm
    def read_multiple(self, points_list, *, points_per_request=25, discover_request=(None, 6)):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    def poll(self, command='start', *, delay=10):
        raise DeviceNotConnected('Must connect to bacnet or database') 
            
    def __contains__(self, value):
        raise DeviceNotConnected('Must connect to bacnet or database') 
          
    def to_excel(self):
        raise DeviceNotConnected('Must connect to bacnet or database') 

    def __setitem__(self, point_name, value):
        raise DeviceNotConnected('Must connect to bacnet or database') 

#    @property
#    def analog_units(self):
#        raise DeviceNotConnected('Must connect to bacnet or database') 
#
#    @property
#    def temperatures(self):
#        raise DeviceNotConnected('Must connect to bacnet or database') 
#
#    @property
#    def percent(self):
#        raise DeviceNotConnected('Must connect to bacnet or database') 
#        
#    @property
#    def multi_states(self):
#        raise DeviceNotConnected('Must connect to bacnet or database') 
#        
#    @property
#    def binary_states(self):
#        raise DeviceNotConnected('Must connect to bacnet or database') 

    def _discoverPoints(self):
        raise DeviceNotConnected('Must connect to bacnet or database')  

    def __repr__(self):
        return '%s / Disconnected' % self.properties.name


class DeviceNotConnected(Exception):
    pass

