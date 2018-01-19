#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
Device.py - describe a BACnet Device

'''
#--- standard Python modules ---
from collections import namedtuple
from datetime import datetime
import weakref

import os.path

#--- 3rd party modules ---
import sqlite3

import pandas as pd
import logging
log = logging.getLogger('BAC0.core.devices')
try:
    from xlwings import Workbook, Sheet, Range, Chart
    _XLWINGS = True
except ImportError:
    log.debug('xlwings not installed. If using Windows or OSX, install to get more features.')
    _XLWINGS = False


#--- this application's modules ---
from bacpypes.basetypes import ServicesSupported

from .Points import NumericPoint, BooleanPoint, EnumPoint, OfflinePoint
from ..io.IOExceptions import NoResponseFromController, SegmentationNotSupported
#from ...bokeh.BokehRenderer import BokehPlot
from ...sql.sql import SQLMixin
from ...tasks.DoOnce import DoOnce
from .mixins.read_mixin import ReadPropertyMultiple, ReadProperty

from ..utils.notes import Notes


#------------------------------------------------------------------------------

class DeviceProperties(object):
    """
    This serves as a container for device properties
    """

    def __init__(self):
        self.name = 'Unknown'
        self.address = None
        self.device_id = None
        self.network = None
        self.pollDelay = None
        self.objects_list = None
        self.pss = ServicesSupported()
        #self.serving_chart = None
        #self.charts = None
        self.multistates = None
        self.db_name = None
        self.segmentation_supported = True

    def __repr__(self):
        return '%s' % self.asdict

    @property
    def asdict(self):
        return self.__dict__


class Device(SQLMixin):
    """
    Represent a BACnet device.  Once defined, it allows use of read, write, sim, release 
    functions to communicate with the device on the network.
    
    :param address: address of the device (ex. '2:5')
    :param device_id: bacnet device ID (boid)
    :param network: defined by BAC0.connect()
    :param poll: (int) if > 0, will poll every points each x seconds.
    :from_backup: sqlite backup file
    :segmentation_supported: (boolean) When segmentation is not supported, BAC0
                             will not use read property multiple to poll the 
                             device.
    :object_list: (list) Use can provide a custom object_list to use for the
                  the creation of the device. the object list must be built
                  using the same pattern returned by bacpypes when polling the
                  objectList property
                  example ::
                      my_obj_list = [('file', 1),
                     ('analogInput', 2),
                     ('analogInput', 3),
                     ('analogInput', 5),
                     ('analogInput', 4),
                     ('analogInput', 0),
                     ('analogInput', 1)]

    :type address: (str)
    :type device_id: int
    :type network: BAC0.scripts.ReadWriteScript.ReadWriteScript
    """
    def __init__(self, address, device_id, network, *, poll=10, 
                 from_backup = None, segmentation_supported = True,
                 object_list = None, auto_save = 6, 
                 clear_history_on_save = False):
        self._log = logging.getLogger('BAC0.core.devices.%s' \
                    % self.__class__.__name__)
        self._log.setLevel(logging.INFO)
                
        self.properties = DeviceProperties()

        self.properties.address = address
        self.properties.device_id = device_id
        self.properties.network = network
        self.properties.pollDelay = poll
        self.properties.name = ''
        self.properties.objects_list = []
        self.properties.pss = ServicesSupported()
        #self.properties.serving_chart = {}
        #self.properties.charts = []
        self.properties.multistates = {}
        self.properties.auto_save = auto_save
        self.properties.clear_history_on_save = clear_history_on_save
        
        self.segmentation_supported = segmentation_supported
        self.custom_object_list = object_list

        self.db = None
        # Todo : find a way to normalize the name of the db
        self.properties.db_name = ''

        self.points = []

        self._polling_task = namedtuple('_polling_task', ['task', 'running'])
        self._polling_task.task = None
        self._polling_task.running = False

        self._notes = Notes("Controller initialized")

        
        if from_backup:
            filename = from_backup
            db_name = filename.split('.')[0]
            if os.path.isfile(filename):
                self.properties.db_name = db_name
                self.new_state(DeviceDisconnected)
            else:
                raise FileNotFoundError("Can't find %s on drive" % filename)
        else:
            self.new_state(DeviceDisconnected)


    def new_state(self, newstate):
        """
        Base of the state machine mechanism.
        Used to make transitions between device states.
        Take care to call the state init function.
        """
        self._log.info('Changing device state to {}'.format(newstate))
        self.__class__ = newstate
        self._init_state()


    def _init_state(self):
        """
        Execute additional code upon state modification
        """
        raise NotImplementedError()


    def connect(self):
        """
        Connect the device to the network
        """
        raise NotImplementedError()


    def disconnect(self):
        raise NotImplementedError()


    def initialize_device_from_db(self):
        raise NotImplementedError()


    @property
    def notes(self):
        """
        Allow the addition of text notes to the device.
        Notes are stored as timeseries (same than points)

        :returns: pd.Series
        """
        return self._notes.get_serie()


    @notes.setter
    def notes(self, note):
        """
        Setter for notes

        :param note: (str)
        """
        self._notes.add(note)


    def df(self, list_of_points, force_read=True):
        """
        Build a pandas DataFrame from a list of points.  DataFrames are used to present and analyze data.

        :param list_of_points: a list of point names as str
        :returns: pd.DataFrame
        """
        raise NotImplementedError()



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
        Read all points from a device into a (Pandas) dataframe (Pandas).  Items are 
        accessible by point name.
        """
        raise NotImplementedError()


    def __getitem__(self, point_name):
        """
        Get a point from its name.
        If a list is passed - a dataframe is returned.

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
        Given a string, interpret the last word as the value, everything else is 
        considered to be the point name.
        """
        args = arg.split()
        pointName = ' '.join(args[:-1])
        value = args[-1]
        return (pointName, value)
    
    def clear_histories(self):
        for point in self.points:
            point.clear_history()

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


    def _findPoint(self, name, force_read=True):
        """
        Helper that retrieve point based on its name.

        :param name: (str) name of the point
        :param force_read: (bool) read value of the point each time the function is called.
        :returns: Point object
        :rtype: BAC0.core.devices.Point.Point (NumericPoint, EnumPoint or BooleanPoint)
        """
        raise NotImplementedError()

        
    def do(self, func):
        DoOnce(func).start()


    def __repr__(self):
        return '%s / Undefined' % self.properties.name


#@fix_docs
class DeviceConnected(Device):
    """
    Find a device on the BACnet network.  Set its state to 'connected'.
    Once connected, all subsequent commands use this BACnet connection.
    """

    def _init_state(self):
        self._buildPointList()            
        self.properties.network.register_device(self)

    def disconnect(self):
        self._log.info('Wait while stopping polling')
        self.poll(command='stop')
        self.properties.network.unregister_device(self)
        self.new_state(DeviceFromDB)


    def connect(self, *, db = None):
        """
        A connected device can be switched to 'database mode' where the device will 
        not use the BACnet network but instead obtain its contents from a previously 
        stored database.
        """
        if db:
            self.poll(command = 'stop')
            self.properties.db_name = db.split('.')[0]
            self.new_state(DeviceFromDB)
        else:
            self._log.warning('Already connected, provide db arg if you want to connect to db')


    def df(self, list_of_points, force_read=True):
        """
        When connected, calling DF should force a reading on the network.
        """
        his = []
        for point in list_of_points:
            try:
                his.append(self._findPoint(
                    point, force_read=force_read).history)
            except ValueError as ve:
                self._log.error('%s' % ve)
                continue

        return pd.DataFrame(dict(zip(list_of_points, his)))


    def _buildPointList(self):
        """
        Upon connection to build the device point list and properties.
        """
        try:
            self.properties.pss.value = self.properties.network.read(
                '{} device {} protocolServicesSupported'.format(self.properties.address, self.properties.device_id))

        except NoResponseFromController as error:
            self._log.error('Controller not found, aborting. ({})'.format(error))
            return ('Not Found', '', [], [])

        except SegmentationNotSupported as error:
            self._log.warning('Segmentation not supported')
            self.segmentation_supported = False
            self.new_state(DeviceDisconnected)

        self.properties.name = self.properties.network.read(
            '{} device {} objectName'.format(self.properties.address, self.properties.device_id))

        self._log.info('Device {}:[{}] found... building points list'.format(self.properties.device_id,self.properties.name))
        try:
            self.properties.objects_list, self.points = self._discoverPoints(self.custom_object_list)
            if self.properties.pollDelay > 0:
                self.poll()
        except NoResponseFromController as error:
            self._log.error('Cannot retrieve object list, disconnecting...')
            self.segmentation_supported = False
            self.new_state(DeviceDisconnected)


    def __getitem__(self, point_name):
        """
        Allows the syntax: device['point_name'] or device[list_of_points]
            
        If calling a list, last value will be used (won't read on the network)
        for performance reasons.
        If calling a simple point, point will be read via BACnet.
        """
        try:
            if isinstance(point_name, list):
                return self.df(point_name, force_read=False)
            else:
                return self._findPoint(point_name)
        except ValueError as ve:
            self._log.error('%s' % ve)


    def __iter__(self):
        for each in self.points:
            yield each


    def __contains__(self, value):
        """
        Allows the syntax:
            if "point_name" in device: 
        """
        return value in self.points_name


    @property
    def points_name(self):
        for each in self.points:
            yield each.properties.name


    def to_excel(self):
        """
        Create an Excel spreadsheet from the device's point histories.
        """
        his = {}
        for name in list(self.points_name):
            try:
                his[name] = self._findPoint(name, force_read=False).history.replace(
                    ['inactive', 'active'], [0, 1]).resample('1ms')
            except TypeError:
                his[name] = self._findPoint(
                    name, force_read=False).history.resample('1ms')

        his['Notes'] = self.notes
        df = pd.DataFrame(his).fillna(method='ffill').fillna(method='bfill')

        if _XLWINGS:
            wb = Workbook()
            Range('A1').value = df
        else:
            df.to_csv()


    def __setitem__(self, point_name, value):
        """
        Allows the syntax: 
            device['point_name'] = value
        """
        try:
            self._findPoint(point_name)._set(value)
        except ValueError as ve:
            self._log.error('%s' % ve)


    def __len__(self):
        """
        Length of a device = number of points
        """
        return len(self.points)


    def _parseArgs(self, arg):
        args = arg.split()
        pointName = ' '.join(args[:-1])
        value = args[-1]
        return (pointName, value)


    @property
    def analog_units(self):
        """
        Shortcut to retrieve all analog points units [Used by Bokeh trending feature]
        """
        au = []
        us = []
        for each in self.points:
            if isinstance(each, NumericPoint):
                au.append(each.properties.name)
                us.append(each.properties.units_state)
        return dict(zip(au, us))


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
        return dict(zip(ms, us))


    @property
    def binary_states(self):
        bs = []
        us = []

        for each in self.points:
            if isinstance(each, BooleanPoint):
                bs.append(each.properties.name)
                us.append(each.properties.units_state)
        return dict(zip(bs, us))
         

    def _findPoint(self, name, force_read=True):
        """
        Used by getter and setter functions
        """
        for point in self.points:
            if point.properties.name == name:
                if force_read:
                    point.value
                return point
        raise ValueError("%s doesn't exist in controller" % name)


    def __repr__(self):
        return '%s / Connected' % self.properties.name


#------------------------------------------------------------------------------

class RPDeviceConnected(DeviceConnected, ReadProperty):
    """
    [Device state] If device is connected but doesn't support ReadPropertyMultiple
    
    BAC0 will not poll such points automatically (since it would cause excessive network traffic).
    Instead manual polling must be used as needed via the poll() function.
    """
    def __str__(self):
        return 'connected [for ReadProperty]'

        
class RPMDeviceConnected(DeviceConnected, ReadPropertyMultiple):
    """
    [Device state] If device is connected and supports ReadPropertyMultiple
    """
    def __str__(self):
        return 'connected [for ReadPropertyMultiple]'


#@fix_docs
class DeviceDisconnected(Device):
    """
    [Device state] Initial state of a device. Disconnected from BACnet.
    """
    def _init_state(self):
        self.connect()


    def connect(self, *, db = None):
        """
        Attempt to connect to device.  If unable, attempt to connect to a controller database  
        (so the user can use previously saved data).
        """
        if db:
            self.properties.db_name = db
        try:
            name = self.properties.network.read('{} device {} objectName'.format(
                    self.properties.address, self.properties.device_id))
            
            segmentation = self.properties.network.read('{} device {} segmentationSupported'.format(
                    self.properties.address, self.properties.device_id))
            
            if not self.segmentation_supported or \
                segmentation not in ('segmentedTransmit', 'segmentedBoth'):
                segmentation_supported = False
                self._log.debug('Segmentation not supported')
            else:
                segmentation_supported = True

            if name:
                if segmentation_supported:
                    self.new_state(RPMDeviceConnected)
                else:
                    self.new_state(RPDeviceConnected)
  
        except SegmentationNotSupported:
            self.segmentation_supported = False
            self._log.warning('Segmentation not supported.... expect slow responses.')
            self.new_state(RPDeviceConnected)

        except (NoResponseFromController, AttributeError) as error:
            if self.properties.db_name:
                self.new_state(DeviceFromDB)
            else:
                self._log.warning('Offline: provide database name to load stored data.')
                self._log.warning("Ex. controller.connect(db = 'backup')")
        

    def df(self, list_of_points, force_read=True):
        raise DeviceNotConnected('Must connect to BACnet or database')


    @property
    def simulated_points(self):
        for each in self.points:
            if each.properties.simulated:
                yield each


    def _buildPointList(self):
        raise DeviceNotConnected('Must connect to BACnet or database')


# This should be a "read" function and rpm defined in state rpm
    def read_multiple(self, points_list, *, points_per_request=25, discover_request=(None, 6)):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def poll(self, command='start', *, delay=10):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def __getitem__(self, point_name):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def __iter__(self):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def __contains__(self, value):
        raise DeviceNotConnected('Must connect to BACnet or database')


    @property
    def points_name(self):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def to_excel(self):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def __setitem__(self, point_name, value):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def __len__(self):
        raise DeviceNotConnected('Must connect to BACnet or database')


    @property
    def analog_units(self):
        raise DeviceNotConnected('Must connect to BACnet or database')


    @property
    def temperatures(self):
        raise DeviceNotConnected('Must connect to BACnet or database')


    @property
    def percent(self):
        raise DeviceNotConnected('Must connect to BACnet or database')


    @property
    def multi_states(self):
        raise DeviceNotConnected('Must connect to bacnet or database')

    @property
    def binary_states(self):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def _discoverPoints(self, custom_object_list = None):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def _findPoint(self, name, force_read=True):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def __repr__(self):
        return '%s / Disconnected' % self.properties.name

#------------------------------------------------------------------------------

#@fix_docs
class DeviceFromDB(DeviceConnected):
    """
    [Device state] Where requests for a point's present value returns the last 
    valid value from the point's history.
    """
    def _init_state(self):
        try:
            self.initialize_device_from_db()
        except ValueError:
            self.new_state(DeviceDisconnected)


    def connect(self, *, network = None, from_backup = None):
        """
        In DBState, a device can be reconnected to BACnet using:
            device.connect(network=bacnet) (bacnet = BAC0.connect())
        """
        if network and from_backup:
            raise WrongParameter('Please provide network OR from_backup')

        elif network:
            self.properties.network = network
            try:
                name = self.properties.network.read('{} device {} objectName'.format(
                        self.properties.address, self.properties.device_id))
            
                segmentation = self.properties.network.read('{} device {} segmentationSupported'.format(
                    self.properties.address, self.properties.device_id))
            
                if not self.segmentation_supported or \
                    segmentation not in ('segmentedTransmit', 'segmentedBoth'):
                    segmentation_supported = False
                    self._log.debug('Segmentation not supported')
                else:
                    segmentation_supported = True
                    
                if name:
                    if segmentation_supported:
                        self.new_state(RPMDeviceConnected)
                    else:
                        self.new_state(RPDeviceConnected)
                    self.db.close()

            except NoResponseFromController:
                self._log.error('Unable to connect, keeping DB mode active')

        elif from_backup:
            self.properties.db_name = from_backup.split('.')[0]
            self._init_state()


    def initialize_device_from_db(self):
        self._log.info('Initializing DB')
        # Save important properties for reuse
        if self.properties.db_name:
            dbname = self.properties.db_name
        else:
            raise ValueError("Please provide db name using device.load_db('name')")
        
        network = self.properties.network
        pss = self.properties.pss
        
        self.db = sqlite3.connect('%s.db' % (self.properties.db_name))
        self._props = self.read_dev_prop(self.properties.db_name)        
        self.points = []
        for point in self.points_from_sql(self.db):
            self.points.append(OfflinePoint(self, point))
        
        self.properties = DeviceProperties()
        self.properties.db_name = dbname
        self.properties.address = self._props['address']
        self.properties.device_id = self._props['device_id']
        self.properties.network = network
        self.properties.pollDelay = self._props['pollDelay']
        self.properties.name = self._props['name']
        self.properties.objects_list = self._props['objects_list']
        self.properties.pss = pss
        self.properties.serving_chart = {}
        self.properties.charts = []
        self.properties.multistates = self._props['multistates']
        print('Device restored from db')


    @property
    def simulated_points(self):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def _buildPointList(self):
        raise DeviceNotConnected('Must connect to BACnet or database')


# This should be a "read" function and rpm defined in state rpm
    def read_multiple(self, points_list, *, points_per_request=25, discover_request=(None, 6)):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def poll(self, command='start', *, delay=10):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def __contains__(self, value):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def to_excel(self):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def __setitem__(self, point_name, value):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def _discoverPoints(self, custom_object_list = None):
        raise DeviceNotConnected('Must connect to BACnet or database')


    def __repr__(self):
        return '%s / Disconnected' % self.properties.name

#------------------------------------------------------------------------------

class DeviceLoad(DeviceFromDB):
    def __init__(self,filename = None):
        if filename:
            Device.__init__(self,None,None,None,from_backup = filename)
        else:
            raise Exception('Please provide backup file as argument')


# Some exceptions
class DeviceNotConnected(Exception):
    pass

class WrongParameter(Exception):
    pass

