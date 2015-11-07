#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
#from ..functions.discoverPoints import discoverPoints

from .Points import NumericPoint, BooleanPoint, EnumPoint
from ..io.IOExceptions import NoResponseFromController, WriteAccessDenied
from ...tasks.Poll import DevicePoll

from collections import namedtuple

try:
    import pandas as pd
    _PANDA = True
except ImportError:
    _PANDA = False


class Device():
    """
    Bacnet device
    This class represents a controller. When defined, it allows
    the use of read, write, sim, release functions to communicate
    with the device on the network
    """

    def __init__(self, addr, devId, network):
        """
        Initialization require address, device id and bacnetApp (the script itself)
        :param addr: address of the device (ex. '2:5')
        :param devId: bacnet device ID (boid)
        :param bacnetApp: the script itself
        """
        self.addr = addr
        self.deviceID = devId
        self.network = network
        self.pollDelay = 10
        self._pointsDF = pd.DataFrame()
        self.name = ''

        self.simPoints = []
        self.points = []
        
        self._polling_task = namedtuple('_polling_task', ['task', 'running'])
        self._polling_task.task = None
        self._polling_task.running = False

        self._buildPointList()
    
    @property
    def simulated_points(self):
        """
        Return a list of simulated points
        Could be a generator ?
        Nice way to test
        """
        raise Exception('Not implemented yet')

    def _buildPointList(self):
        """
        Read all points of the device and creates a dataframe (Pandas) to store
        the list and allow quick access.
        This list will be used to access variables based on point name
        """
        result = self._discoverPoints()
        self._pointsDF = result[3]
        self.name = result[0]
        self.points = result[4]

    def read(self, args):
        """
        Read presentValue of a point from a device

        :param args: point name
        :returns: value read
        """
        pointName = args
        try:
            val = self.network.read(
                '%s %s %s presentValue' %
                (self.addr, self._pointsDF.ix[pointName].pointType, str(
                    self._pointsDF.ix[pointName].pointAddress)))
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)
        return val
        
    def read_multiple(self, point_list, chunk_length=25):  
        def chunks(thing, chunk_length):
            """Iterate through thing in chunks of size chunk_length.
        
            Note that the last chunk can be smaller than chunk_length.
            """
            for i in range(0, len(thing), chunk_length):
                yield thing[i:i+chunk_length]                              
        
        for batch in chunks(point_list,chunk_length): 
            request = ''
            points = []
            str_list = []
            for each in batch:
                point = self._findPoint(each, force_read = False)
                points.append(point)
                str_list.append(' ' + point.properties.type)
                str_list.append(' ' + str(point.properties.address))
                str_list.append(' presentValue')
                rpm_param = (''.join(str_list))  
                request = '%s %s' % (self.addr, rpm_param)
                #print('Request : %s' % request)
            try:
                val = self.network.readMultiple(request)
            except KeyError as error:
                raise Exception('Unknown point name : %s' % error)
            points_values = zip(points, val)
            for each in points_values:
                each[0]._trend(each[1])
        
            

    def write(self, args):
        """
        Write to present value of a point of a device

        :param args: (str) pointName value (both info in same string)

        """
        pointName, value = self._convert_write_arguments(args)
        try:
            self.network.write(
                '%s %s %s presentValue %s' %
                (self.addr, self._pointsDF.ix[pointName].pointType, str(
                    self._pointsDF.ix[pointName].pointAddress), value))
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)

    def default(self, args):
        """
        Write to relinquish default value of a point of a device

        :param args: (str) pointName value (both info in same string)

        """
        pointName, value = self._convert_write_arguments(args)
        # Accept boolean value
        try:
            self.network.write(
                '%s %s %s relinquishDefault %s' %
                (self.addr, self._pointsDF.ix[pointName].pointType, str(
                    self._pointsDF.ix[pointName].pointAddress), value))
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)

    def sim(self, args):
        """
        Simulate a value
        Will write to out_of_service property (true)
        Will then write the presentValue so the controller will use that value
        The point name will be added to the list of simulated points
        (self.simPoints)

        :param args: (str) pointName value (both info in same string)

        """
        pointName, value = self._convert_write_arguments(args)
        try:
            self.network.sim(
                '%s %s %s presentValue %s' %
                (self.addr, self._pointsDF.ix[pointName].pointType, str(
                    self._pointsDF.ix[pointName].pointAddress), value))
            if pointName not in self.simPoints:
                self.simPoints.append(pointName)
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)

    # TODO : Move this function inside Point
    # New function shoudl iterate points and call point.release
    def releaseAllSim(self):
        """
        Release all points stored in the self.simPoints variable
        Will write to out_of_service property (false)
        The controller will take control back of the presentValue
        """
        for pointName in self.simPoints:
            try:
                self.network.release(
                    '%s %s %s' %
                    (self.addr, self._pointsDF.ix[pointName].pointType, str(
                        self._pointsDF.ix[pointName].pointAddress)))
                if pointName in self.simPoints:
                    self.simPoints.pop(pointName)
            except KeyError:
                raise Exception('Unknown point name : %s' % pointName)

    def release(self, args):
        """
        Release points
        Will write to out_of_service property (false)
        The controller will take control back of the presentValue

        :param args: (str) pointName
        """

        pointName = args
        try:
            self.network.release(
                '%s %s %s' %
                (self.addr, self._pointsDF.ix[pointName].pointType, str(
                    self._pointsDF.ix[pointName].pointAddress)))
            if pointName in self.simPoints:
                self.simPoints.remove(pointName)
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)

    def ovr(self, args):
        """
        Override the output (Make manual operator command on point at priority 8)

        :param args: (str) pointName value (both info in same string)

        """
        pointName, value = self._convert_write_arguments(args)
        try:
            self.network.write(
                '%s %s %s presentValue %s - 8' %
                (self.addr, self._pointsDF.ix[pointName].pointType, str(
                    self._pointsDF.ix[pointName].pointAddress), value))
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)

    def auto(self, args):
        """
        Release the override on the output (Write null on point at priority 8)

        :param args: (str) pointName value (both info in same string)

        """
        pointName = args
        try:
            self.network.write(
                '%s %s %s presentValue null - 8' %
                (self.addr, self._pointsDF.ix[pointName].pointType, str(
                    self._pointsDF.ix[pointName].pointAddress)))
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)

    def get(self, name):
        """
        Get a point based on its name

        :param name: (str) pointName
        :returns: (Point) the point (can be Numeric, Boolean or Enum)
        """
        return self._findPoint(name)

    def poll(self, command='start', *, delay=10):
        """
        Enable polling of a variable. Will be read every x seconds (delay=x sec)
        Can be stopped by using point.poll('stop') or .poll(0) or .poll(False)
        or by setting a delay = 0
        """
        if str(command).lower() == 'stop' \
                or command == False \
                or command == 0 \
                or delay == 0:
            if isinstance(self._polling_task.task, DevicePoll):
                self._polling_task.task.stop()
                self._polling_task.task = None
                self._polling_task.running = False
        elif self._polling_task.task is None:
            self._polling_task.task = DevicePoll(self, delay=delay)
            self._polling_task.task.start()
            self._polling_task.running = True
        elif self._polling_task.running:
            self._polling_task.task.stop()
            self._polling_task.running = False
            self._polling_task.task = DevicePoll(self, delay=delay)
            self._polling_task.task.start()
            self._polling_task.running = True
        else:
            raise RuntimeError('Stop polling before redefining it')
        
    def __getitem__(self,key):
        """
        Get a point based on its name

        :param name: (str) pointName
        :returns: (Point) the point (can be Numeric, Boolean or Enum)
        """
        # Read point value and store it
        #self._findPoint(key).value
        # return the point itself
        return self._findPoint(key)
        
    def __iter__(self):
        pass
        
    def __setitem__(self, key, value):
        """
        Write, sim or ovr value
        """
        self._findPoint(key)._set(value)

    def __len__(self):
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

    def _convert_write_arguments(self, args):
        """
        This allow the use of enum state or boolean state for wirting to points
        ex. device.write('name True') instead of device.write('name active')
        """
        #TODO : Verify value is float or int for analog        
        pointName, value = self._parseArgs(args)
        # Accept boolean value
        if 'binary' in self._pointsDF.ix[pointName].pointType:
            if value.lower() == 'false':
                value = 'inactive'
            elif value.lower() == 'true':
                value = 'active'
        # Accept states as value if multiState
        if 'multiState' in self._pointsDF.ix[pointName].pointType:
            state_list = [states.lower() for states in self._pointsDF.ix[
                pointName].units_state]
            if value.lower() in state_list:
                value = state_list.index(value.lower()) + 1
        return (pointName, value)

    def _discoverPoints(self):
        """
        This function allows the discovery of all bacnet points in a device

        :param bacnetApp: The app itself so we can call read
        :param address: address of the device as a string (ex. '2:5')
        :param devID: device ID of the bacnet device as a string (ex. '1001')

        :returns: a tuple with deviceName, pss, objList, df

        *deviceName* : name of the device
        *pss* : protocole service supported
        *objList* : list of bacnet object (ex. analogInput, 1)
        *df* : is a dataFrame containing pointType, pointAddress, pointName, description
        presentValue and units

        If pandas can't be found, df will be a simple array

        """
        try:
            pss = self.network.read(
                '%s device %s protocolServicesSupported' %
                (self.addr, self.deviceID))
        except NoResponseFromController as error:
            print('Controller not found, aborting. (%s)' % error)
            return ('Not Found', '', [], [], [])
        deviceName = self.network.read(
            '%s device %s objectName' %
            (self.addr, self.deviceID))
        print('Found %s... building points list' % deviceName)
        objList = self.network.read(
            '%s device %s objectList' %
            (self.addr, self.deviceID))
        newLine = []
        result = []
        points = []

        for pointType, pointAddr in objList:
            if str(pointType) not in 'file calendar device schedule notificationClass eventLog trendLog loop program eventEnrollment' and not isinstance(
                    pointType, int) and pointType is not None:
                if 'binary' not in str(
                        pointType) and 'multiState' not in str(pointType):
                    newLine = [pointType, pointAddr]
                    newLine.extend(
                        self.network.readMultiple(
                            '%s %s %s objectName description presentValue units' %
                            (self.addr, pointType, pointAddr)))
                    points.append(
                        NumericPoint(
                            pointType=newLine[0],
                            pointAddress=newLine[1],
                            pointName=newLine[2],
                            description=newLine[3],
                            presentValue=newLine[4],
                            units_state=newLine[5],
                            device=self))
                elif 'binary' in str(pointType):
                    newLine = [pointType, pointAddr]
                    infos = (
                        self.network.readMultiple(
                            '%s %s %s objectName description presentValue inactiveText activeText' %
                            (self.addr, pointType, pointAddr)))
                    newLine.extend(infos[:-2])
                    newLine.extend([infos[-2:]])
                    points.append(
                        BooleanPoint(
                            pointType=newLine[0],
                            pointAddress=newLine[1],
                            pointName=newLine[2],
                            description=newLine[3],
                            presentValue=newLine[4],
                            units_state=newLine[5],
                            device=self))
                elif 'multiState' in str(pointType):
                    newLine = [pointType, pointAddr]
                    newLine.extend(
                        self.network.readMultiple(
                            '%s %s %s objectName description presentValue stateText' %
                            (self.addr, pointType, pointAddr)))
                    points.append(
                        EnumPoint(
                            pointType=newLine[0],
                            pointAddress=newLine[1],
                            pointName=newLine[2],
                            description=newLine[3],
                            presentValue=newLine[4],
                            units_state=newLine[5],
                            device=self))
                result.append(newLine)

        if _PANDA:
            df = pd.DataFrame(
                result,
                columns=[
                    'pointType',
                    'pointAddress',
                    'pointName',
                    'description',
                    'presentValue',
                    'units_state']).set_index(
                ['pointName'])
        else:
            df = result

        print('Ready!')
        return (deviceName, pss, objList, df, points)

    def _findPoint(self, name, force_read = True):
        """
        Helper that retrieve point based on its name.
        """
        for point in self.points:
            if point.properties.name == name:
                if force_read:
                    point.value
                return point
        raise ValueError("%s doesn't exist in controller" % name)
        
    def __repr__(self):
        return '%s' % self.name
