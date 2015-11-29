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

from .Points import NumericPoint, BooleanPoint, EnumPoint
from ..io.IOExceptions import NoResponseFromController, ReadPropertyMultipleException
from ...tasks.Poll import DevicePoll
from ...tasks.BokehRenderer import BokehRenderer

from collections import namedtuple
import pandas as pd
from datetime import datetime


class Device():
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
        self.properties = namedtuple('properties',
                                     ['name', 'address', 'device_id', 'network',
                                      'pollDelay', 'objects_list', 'pss',
                                      'serving_chart', 'charts', 'multistates'])
        self.properties.address = address
        self.properties.device_id = device_id
        self.properties.network = network
        self.properties.pollDelay = 10
        self.properties.name = ''
        self.properties.objects_list = []
        self.properties.pss = ServicesSupported()
        self.properties.serving_chart = {}
        self.properties.charts = []
        self.properties.multistates = {}

        self.points = []

        self._polling_task = namedtuple('_polling_task', ['task', 'running'])
        self._polling_task.task = None
        self._polling_task.running = False

        self._buildPointList()
        if poll > 0:
            self.poll()

        self._notes = namedtuple('_notes',
                                   ['timestamp', 'notes'])

        self._notes.timestamp = []
        self._notes.notes = []
        self._notes.notes.append("Controller initialized")
        self._notes.timestamp.append(datetime.now())
            
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
        
    def df(self, list_of_points):
        """
        df is a way to build a pandas DataFrame from a list of points
        DataFrame can be used to present data or analysis
        
        :param list_of_points: a list of point names as str
        :returns: pd.DataFrame
        """
        his = []
        for point in list_of_points:
            his.append(self._findPoint(point).history)
    
        return pd.DataFrame(dict(zip(list_of_points,his)))
        
    def chart(self, list_of_points, *, title = 'New'):
        """
        chart offers a way to draw a chart from a list of points.
        It allows to pass args to the pandas plot() functions
        refer to the pandas and matplotlib doc for details.
        :param list_of_points: a list of point name as str
        :param plot_args: arg for plot function
        :returns: plot()
        """
        if title in self.properties.charts:
            self.properties.serving_chart[title].exitFlag = True
            del self.properties.serving_chart[title]
        else:
            self.properties.serving_chart[title] = BokehRenderer(self,list_of_points, title = title)
            self.properties.serving_chart[title].start()
            
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

    def _batches(self, request, points_per_request):
        """
        Generator that creates request batches.
        Each batch will contain a maximum of
        "points_per_request" points to read.
        :params: request a list of point_name as a list
        :params: (int) points_per_request
        :returns: (iter) list of point_name of size <= points_per_request
        """
        for i in range(0, len(request), points_per_request):
            yield request[i:i + points_per_request]

    def _rpm_request_by_name(self, point_list):
        """
        :param point_list: a list of point
        :returns: (tuple) read request for each points, points
        """
        points = []
        requests = []
        for each in point_list:
            str_list = []
            point = self._findPoint(each, force_read=False)
            points.append(point)
            str_list.append(' ' + point.properties.type)
            str_list.append(' ' + str(point.properties.address))
            str_list.append(' presentValue')
            rpm_param = (''.join(str_list))
            requests.append(rpm_param)
        return (requests, points)

    def read_multiple(self, points_list, *, points_per_request=25, discover_request=(None, 6)):
        """
        Functions to read points from a device using the read property
        multiple request.
        Using readProperty request can be very slow to read a lot of data.

        :param points_list: (list) a list of all point_name as str
        :param points_per_request: (int) number of points in the request

        Using too many points will create big requests needing segmentation.
        It's better to use just enough request so the message will not require
        segmentation.

        :Example:

        device.read_multiple(['point1', 'point2', 'point3'], points_per_request = 10)
        """
        if not self.properties.pss['readPropertyMultiple']:
            raise ReadPropertyMultipleException('Not supported on device')
        if discover_request[0]:
            values = []
            info_length = discover_request[1]
            big_request = discover_request[0]
            # print(big_request)
            for request in self._batches(big_request,
                                         points_per_request):
                try:
                    
                    request = ('%s %s' %
                               (self.properties.address, ''.join(request)))
                                        
                    val = self.properties.network.readMultiple(request)
                except KeyError as error:
                    raise Exception('Unknown point name : %s' % error)
                # Save each value to history of each point
                for points_info in self._batches(val, info_length):
                    values.append(points_info)
            return values
        else:
            big_request = self._rpm_request_by_name(points_list)
            i = 0
            for request in self._batches(big_request[0],
                                         points_per_request):
                try:
                    request = ('%s %s' %
                               (self.properties.address, ''.join(request)))
                    val = self.properties.network.readMultiple(request)
                    points_values = zip(big_request[1][i:i + len(val)], val)
                    i += len(val)
                    for each in points_values:
                        each[0]._trend(each[1])
                except KeyError as error:
                    raise Exception('Unknown point name : %s' % error)
                # Save each value to history of each point

    def poll(self, command='start', *, delay=10):
        """
        Enable polling of a variable. Will be read every x seconds (delay=x sec)
        Can be stopped by using point.poll('stop') or .poll(0) or .poll(False)
        or by setting a delay = 0

        :param command: (str) start or stop polling
        :param delay: (int) time delay between polls in seconds
        :type command: str
        :type delay: int

        :Example:

        device.poll()
        device.poll('stop')
        device.poll(delay = 5)
        """
        if str(command).lower() == 'stop' \
                or command == False \
                or command == 0 \
                or delay == 0:
            if isinstance(self._polling_task.task, DevicePoll):
                self._polling_task.task.stop()
                self._polling_task.task = None
                self._polling_task.running = False
                print('Polling stopped')
        elif self._polling_task.task is None:
            self._polling_task.task = DevicePoll(self, delay=delay)
            self._polling_task.task.start()
            self._polling_task.running = True
            print('Polling started, every values read each %s seconds' % delay)
        elif self._polling_task.running:
            self._polling_task.task.stop()
            self._polling_task.running = False
            self._polling_task.task = DevicePoll(self, delay=delay)
            self._polling_task.task.start()
            self._polling_task.running = True
            print('Polling started, every values read each %s seconds' % delay)
        else:
            raise RuntimeError('Stop polling before redefining it')

    def __getitem__(self, point_name):
        """
        Get a point based on its name
        If a list is passed, will return a dataframe

        :param point_name: (str) name of the point or list of point_names
        :type point_name: str     
        :returns: (Point) the point (can be Numeric, Boolean or Enum) or pd.DataFrame
        """
        if isinstance(point_name,list):
            return self.df(point_name)
        else:
            return self._findPoint(point_name)

    def __iter__(self):
        """
        When iterating a device, iterate points of it.
        """
        for each in self.points:
            yield each
            
    def __contains__(self, value):
        "When using in..."
        return value in self.points_name

    @property
    def points_name(self):
        """
        When iterating a device, iterate points of it.
        """
        for each in self.points:
            yield each.properties.name

    def __setitem__(self, point_name, value):
        """
        Write, sim or ovr value
        :param point_name: Name of the point to set
        :param value: value to write to the point
        :type point_name: str
        :type value: float
        """
        self._findPoint(point_name)._set(value)

    def __len__(self):
        """
        Will return number of points available
        """
        return len(self.points)

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
        au = []
        us = []
        for each in self.points:
            if isinstance(each, NumericPoint):
                au.append(each.properties.name)
                us.append(each.properties.units_state)
        return dict(zip(au,us))
        
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
        """
        Helper that retrieve point based on its name.

        :param name: (str) name of the point
        :param force_read: (bool) read value of the point each time the func
                            is called.
        :returns: Point object
        :rtype: BAC0.core.devices.Point.Point (NumericPoint, EnumPoint or
        BooleanPoint)

        """
        for point in self.points:
            if point.properties.name == name:
                if force_read:
                    point.value
                return point
        raise ValueError("%s doesn't exist in controller" % name)

    def __repr__(self):
        return '%s' % self.properties.name
