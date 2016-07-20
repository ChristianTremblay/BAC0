#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.

from ....tasks.Poll import DevicePoll
from ...io.IOExceptions import ReadPropertyMultipleException, NoResponseFromController, SegmentationNotSupported
from ..Points import NumericPoint, BooleanPoint, EnumPoint, OfflinePoint


class ReadPropertyMultiple():
    """
    This is a Mixin that will handle ReadProperty and ReadPropertyMultiple
    for a device
    """
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
        #print('PSS : %s' % self.properties.pss['readPropertyMultiple']) 
        if not self.properties.pss['readPropertyMultiple']:
            print('Read property Multiple Not supported')
            self.read_single(points_list,points_per_request=1, discover_request=discover_request)
        else:
            if not self.properties.segmentation_supported:
                points_per_request = 1
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
                        if val == None:
                            self.properties.segmentation_supported = False
                            raise SegmentationNotSupported
                    except KeyError as error:
                        raise Exception('Unknown point name : %s' % error)
                        
                    except SegmentationNotSupported as error:
                        self.properties.segmentation_supported = False
                        self.read_multiple(points_list,points_per_request=1, discover_request=discover_request)
                        print('Seg not supported')                        
                    # Save each value to history of each point
                    else:
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
                    except SegmentationNotSupported as error:
                        self.properties.segmentation_supported = False
                        self.read_multiple(points_list,points_per_request=1, discover_request=discover_request)
                        # Save each value to history of each point
                    except KeyError as error:
                        raise Exception('Unknown point name : %s' % error)
                    # Save each value to history of each point
                    else:
                        points_values = zip(big_request[1][i:i + len(val)], val)
                        i += len(val)
                        for each in points_values:
                            each[0]._trend(each[1])
                        
    def read_single(self, points_list, *, points_per_request=1, discover_request=(None, 4)):
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
    
                    val = self.properties.network.read(request)
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
                    val = self.properties.network.read(request)
                    points_values = zip(big_request[1][i:i + len(val)], val)
                    i += len(val)
                    for each in points_values:
                        each[0]._trend(each[1])
                except KeyError as error:
                    raise Exception('Unknown point name : %s' % error)
                # Save each value to history of each point

    def _discoverPoints(self):
        try : 
            objList = self.properties.network.read(
                '%s device %s objectList' %
                (self.properties.address, self.properties.device_id))
        except SegmentationNotSupported:
            objList = []
            number_of_objects = self.properties.network.read(
                '%s device %s objectList' %
                (self.properties.address, self.properties.device_id), arr_index = 0)
            for i in range(1,number_of_objects+1):
                objList.append(self.properties.network.read(
                '%s device %s objectList' %
                (self.properties.address, self.properties.device_id), arr_index = i))
            

        points = []
        #print(objList)
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
        try:
            analog_points_info = self.read_multiple(
                '', discover_request=(analog_request, 4), points_per_request=5)
        except SegmentationNotSupported:
            raise
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
            if len(point_infos) == 3:
                #we probably get only objectName, presentValue and description
                point_units_state = ('OFF', 'ON')
                point_description = point_infos[2]
            elif len(point_infos) == 5:
                point_units_state = (point_infos[2], point_infos[3])           
                try:
                    point_description = point_infos[4]
                except IndexError:
                    point_description = ""
            elif len(point_infos) == 2:
                point_units_state = ('OFF', 'ON')          
                point_description = ""
            else:
                #raise ValueError('Not enough values returned', each, point_infos)
                # SHOULD SWITCH TO SEGMENTATION_SUPPORTED = FALSE HERE
                print('Cannot add %s / %s' % (point_type, point_address))
                continue
            i += 1
            points.append(
                BooleanPoint(
                    pointType=point_type,
                    pointAddress=point_address,
                    pointName=point_infos[0],
                    description=point_description,
                    presentValue=point_infos[1],
                    units_state=point_units_state,
                    device=self))
        print('Ready!')
        return (objList, points)
            
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
                while self._polling_task.task.is_alive():
                    pass
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
            while self._polling_task.task.is_alive():
                pass
            self._polling_task.running = False
            self._polling_task.task = DevicePoll(self, delay=delay)
            self._polling_task.task.start()
            self._polling_task.running = True
            print('Polling started, every values read each %s seconds' % delay)
        else:
            raise RuntimeError('Stop polling before redefining it')

class ReadProperty():
    """
    This is a Mixin that will handle ReadProperty and ReadPropertyMultiple
    for a device
    """
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

    def read_multiple(self, points_list, *, points_per_request=1, discover_request=(None, 6)):
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
        #print('PSS : %s' % self.properties.pss['readPropertyMultiple'])
        if isinstance(points_list, list):
            for each in points_list:
                self.read_single(each,points_per_request=1, discover_request=discover_request)
        else:
            self.read_single(points_list,points_per_request=1, discover_request=discover_request)
                        
    def read_single(self, request, *, points_per_request=1, discover_request=(None, 4)):
        try:
            request = ('%s %s' %
                               (self.properties.address, ''.join(request)))
            return self.properties.network.read(request)
        except KeyError as error:
            raise Exception('Unknown point name : %s' % error)
        except NoResponseFromController as error:
            return ''
        # Save each value to history of each point
            

    def _discoverPoints(self):
        try : 
            objList = self.properties.network.read(
                '%s device %s objectList' %
                (self.properties.address, self.properties.device_id))
        except SegmentationNotSupported:
            objList = []
            number_of_objects = self.properties.network.read(
                '%s device %s objectList' %
                (self.properties.address, self.properties.device_id), arr_index = 0)
            for i in range(1,number_of_objects+1):
                objList.append(self.properties.network.read(
                '%s device %s objectList' %
                (self.properties.address, self.properties.device_id), arr_index = i))

        points = []

        def retrieve_type(obj_list, point_type_key):
            """
            retrive analog values
            """
            for point_type, point_address in obj_list:
                if point_type_key in point_type:
                    yield (point_type, point_address)

        # Numeric
        for each in retrieve_type(objList, 'analog'):
            point_type = str(each[0])
            point_address = str(each[1])

            points.append(
                NumericPoint(
                    pointType=point_type,
                    pointAddress=point_address,
                    pointName=self.read_single('%s %s objectName ' %
                                  (point_type, point_address)),
                    description=self.read_single('%s %s description ' %
                                  (point_type, point_address)),
                    presentValue=float(self.read_single('%s %s presentValue ' %
                                  (point_type, point_address)),),
                    units_state=self.read_single('%s %s units ' %
                                  (point_type, point_address)),
                    device=self))

        for each in retrieve_type(objList, 'multi'):
            point_type = str(each[0])
            point_address = str(each[1])

            points.append(
                EnumPoint(
                    pointType=point_type,
                    pointAddress=point_address,
                    pointName=self.read_single('%s %s objectName ' %
                                  (point_type, point_address)),
                    description=self.read_single('%s %s description ' %
                                  (point_type, point_address)),
                    presentValue=(self.read_single('%s %s presentValue ' %
                                  (point_type, point_address)),),
                    units_state=self.read_single('%s %s stateText ' %
                                  (point_type, point_address)),
                    device=self))

        for each in retrieve_type(objList, 'binary'):
            point_type = str(each[0])
            point_address = str(each[1])

            points.append(
                BooleanPoint(
                    pointType=point_type,
                    pointAddress=point_address,
                    pointName=self.read_single('%s %s objectName ' %
                                  (point_type, point_address)),
                    description=self.read_single('%s %s description ' %
                                  (point_type, point_address)),
                    presentValue=(self.read_single('%s %s presentValue ' %
                                  (point_type, point_address)),),
                    units_state=(
                                (self.read_single('%s %s inactiveText ' %
                                  (point_type, point_address))),
                                (self.read_single('%s %s activeText ' %
                                  (point_type, point_address)))
                                 ), 
                    device=self))

        print('Ready!')
        return (objList, points)
            
    def poll(self, command='start', *, delay=60):
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
        print('Device too slow, use single points polling if needed')
        print('Points will be read once...')
        for each in self.points:
            each.value
        print('Complete')
